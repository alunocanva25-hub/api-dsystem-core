import json
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session
from app.models.business import Appointment, Customer, TransactionRecord, Professional, ServiceCatalog
from app.models.logs import SyncLog


def _first(data: dict[str, Any], *keys: str, default=None):
    for key in keys:
        value = data.get(key)
        if value is not None and value != "":
            return value
    return default


def _external_id(data: dict[str, Any]) -> str | None:
    # Identificador genérico do registro.
    # Mantém compatibilidade com versões anteriores, mas os clientes do Studio
    # possuem uma regra específica em _customer_code para preservar STR0000.
    value = _first(data, "external_id", "local_id", "id", "codigo", "cod_cliente", "codcliente", "cod_agendamento", "cod_lancamento")
    if value is None or value == "":
        return None
    return str(value)


def _looks_like_generated_client_code(value: Any) -> bool:
    txt = str(value or "").strip().upper()
    if not txt:
        return False
    return txt.startswith(("CLI-", "CLI_", "API_CLIENT_", "GO_CLIENT_"))


def _customer_code(data: dict[str, Any]) -> str | None:
    """Preserva a sigla/código original do DSYSTEM STUDIO.

    O Studio usa códigos como STR0000. A API não deve trocar isso por CLI-X.
    Prioridade: aliases explícitos do Studio; external_id só entra primeiro quando
    não parecer código gerado pela API/GO.
    """
    studio_value = _first(
        data,
        "studio_code", "codigo_studio", "codigo_cliente", "cliente_codigo",
        "client_code", "customer_code", "sigla", "sigla_cliente",
        "codigo", "cod_cliente", "codcliente",
    )
    external = _first(data, "external_id", "local_id", "id")

    # Se external_id veio com STR0000, preserva. Se veio CLI-X, preferir o código do Studio.
    if external and not _looks_like_generated_client_code(external):
        ext_txt = str(external).strip()
        if ext_txt.upper().startswith("STR") or not studio_value:
            return ext_txt
    if studio_value is not None and studio_value != "":
        return str(studio_value).strip()
    if external is not None and external != "":
        return str(external).strip()
    return None


def _with_customer_code_aliases(data: dict[str, Any], code: str | None) -> dict[str, Any]:
    enriched = dict(data)
    if code:
        # Mantém todos os aliases para GO, Studio e conferência no Swagger.
        enriched.setdefault("external_id", code)
        enriched.setdefault("codigo", code)
        enriched.setdefault("sigla", code)
        enriched.setdefault("client_code", code)
        enriched.setdefault("customer_code", code)
        enriched.setdefault("studio_code", code)
    return enriched


def _cancel_status(data: dict[str, Any]) -> bool:
    value = _first(data, "sync_status", "status", "situacao", "situação", "cancelled", "canceled", default="")
    txt = str(value or "").strip().lower()
    txt = txt.replace("í", "i").replace("é", "e").replace("ê", "e").replace("á", "a").replace("ã", "a").replace("ç", "c")
    return txt in {"cancelado", "cancelada", "cancelled", "canceled", "excluido", "excluida", "deleted", "removido", "removida"}


def _bool_deleted(data: dict[str, Any]) -> bool:
    value = _first(data, "is_deleted", "deleted", "excluido", "excluida", default=False)
    if isinstance(value, bool):
        return value or _cancel_status(data)
    if isinstance(value, (int, float)):
        return bool(value) or _cancel_status(data)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "sim", "s", "yes", "y", "excluido", "excluida", "deleted", "cancelado", "cancelada", "cancelled", "canceled"} or _cancel_status(data)
    return _cancel_status(data)


def _enrich_deleted_payload(data: dict[str, Any], *, sync_source: str, deleted_at_value) -> dict[str, Any]:
    enriched = dict(data)
    if _bool_deleted(enriched):
        deleted_at_text = deleted_at_value.isoformat() if hasattr(deleted_at_value, "isoformat") else str(deleted_at_value)
        source_value = str(_first(enriched, "source", "sync_source", default=sync_source) or sync_source)
        if source_value in {"api_local", "desktop_sync"}:
            # Exclusões recebidas por rotas compatíveis do GO devem voltar para o Studio como go_mobile.
            source_value = "go_mobile" if str(sync_source) == "go_mobile" else source_value
        enriched.update({
            "deleted": True,
            "is_deleted": True,
            "deleted_at": enriched.get("deleted_at") or deleted_at_text,
            "status": enriched.get("status") or "cancelado",
            "sync_status": enriched.get("sync_status") or "cancelado",
            "last_source": enriched.get("last_source") or source_value,
            "source": enriched.get("source") or source_value,
            "sync_source": enriched.get("sync_source") or source_value,
            "desktop_imported": False,
            "pending_desktop_pull": True,
            "imported": False,
        })
    return enriched


def _deleted_at(data: dict[str, Any]):
    value = _first(data, "deleted_at", "data_exclusao", "deletedAt")
    if not value:
        return datetime.now(timezone.utc) if _bool_deleted(data) else None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)


def _normalize_type(value: Any) -> str:
    txt = str(value or "").strip().lower()
    txt = txt.replace("í", "i").replace("é", "e").replace("ê", "e").replace("á", "a").replace("ã", "a").replace("ç", "c")
    if txt in {"entrada", "income", "credit", "credito", "receita", "in", "e", "+", "positivo", "receber", "a receber"}:
        return "entrada"
    if txt in {"saida", "expense", "debit", "debito", "despesa", "out", "s", "-", "negativo", "pagar", "a pagar"}:
        return "saida"
    return txt or "entrada"


def _amount(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    txt = str(value).strip().replace("R$", "").replace(" ", "")
    if "," in txt and "." in txt:
        txt = txt.replace(".", "").replace(",", ".")
    elif "," in txt:
        txt = txt.replace(",", ".")
    try:
        return float(txt)
    except Exception:
        return 0.0


def _base_fields(company_id: int, module_code: str, sync_source: str, data: dict[str, Any]) -> dict[str, Any] | None:
    external_id = _external_id(data)
    if not external_id:
        return None
    deleted = _bool_deleted(data)
    deleted_at_value = _deleted_at(data)
    enriched_payload = _enrich_deleted_payload(data, sync_source=sync_source, deleted_at_value=deleted_at_value)
    final_sync_source = str(_first(enriched_payload, "sync_source", "source", default=sync_source) or sync_source)
    return {
        "company_id": company_id,
        "module_code": str(_first(data, "module_code", default=module_code) or module_code),
        "external_id": external_id,
        "sync_source": final_sync_source,
        "is_deleted": deleted,
        "deleted_at": deleted_at_value,
        "external_created_at": _first(data, "created_at", "dtcriacao", "data_criacao"),
        "external_updated_at": _first(data, "updated_at", "dtalteracao", "data_alteracao"),
        "raw_payload": json.dumps(enriched_payload, ensure_ascii=False, default=str),
    }


def _customer_values(company_id: int, module_code: str, sync_source: str, data: dict[str, Any]):
    # Cliente tem contrato especial: o código original do Studio (STR0000)
    # deve ser o external_id e deve aparecer também como codigo/sigla/client_code.
    code = _customer_code(data)
    normalized_data = _with_customer_code_aliases(data, code)
    base = _base_fields(company_id, module_code, sync_source, normalized_data)
    if not base:
        return None
    if code:
        base["external_id"] = code
        payload = json.loads(base.get("raw_payload") or "{}")
        payload = _with_customer_code_aliases(payload, code)
        base["raw_payload"] = json.dumps(payload, ensure_ascii=False, default=str)
    name = _first(data, "name", "nome", "cliente", "full_name", "razao_social", default="Cliente sem nome")
    base.update({
        "name": str(name),
        "phone": _first(data, "phone", "telefone", "celular", "whatsapp"),
        "email": _first(data, "email", "e_mail"),
        "document": _first(data, "document", "cpf", "cnpj", "documento"),
        "notes": _first(data, "notes", "observacao", "observações", "obs"),
    })
    return base


def _appointment_values(company_id: int, module_code: str, sync_source: str, data: dict[str, Any]):
    base = _base_fields(company_id, module_code, sync_source, data)
    if not base:
        return None
    base.update({
        "customer_external_id": _first(data, "customer_external_id", "client_uid", "cliente_id", "id_cliente", "cod_cliente", "codcliente", "codigo_cliente", "cliente_codigo", "client_code", "customer_code", "sigla_cliente"),
        "customer_name": _first(data, "customer_name", "cliente_nome", "cliente", "nome_cliente"),
        "professional_name": _first(data, "professional_name", "profissional", "nome_profissional"),
        "service_name": _first(data, "service_name", "servico", "serviço", "nome_servico"),
        "start_at": _first(data, "start_at", "inicio", "data_hora", "data_agendamento", "scheduled_at"),
        "end_at": _first(data, "end_at", "fim", "data_hora_fim"),
        "status": _first(data, "status", "situacao", "situação"),
        "notes": _first(data, "notes", "observacao", "observações", "obs"),
    })
    return base


def _transaction_values(company_id: int, module_code: str, sync_source: str, data: dict[str, Any]):
    base = _base_fields(company_id, module_code, sync_source, data)
    if not base:
        return None
    base.update({
        "transaction_type": _normalize_type(_first(data, "transaction_type", "kind", "type", "tipo", "natureza", "movimento", "tipo_movimento", "tipo_lancamento")),
        "description": str(_first(data, "description", "descricao", "descrição", "historico", "histórico", "nome", default="Lançamento financeiro")),
        "amount": _amount(_first(data, "amount", "value", "valor", "total", "vl_total", "preco", "preço")),
        "category": _first(data, "category", "categoria", "grupo", "classificacao", "classificação"),
        "payment_method": _first(data, "payment_method", "forma_pagamento", "pagamento", "forma"),
        "transaction_date": _first(data, "transaction_date", "occurred_at", "date", "data", "dt_lancamento", "created_at"),
        "customer_external_id": _first(data, "customer_external_id", "client_uid", "cliente_id", "id_cliente", "cod_cliente", "codcliente", "codigo_cliente", "cliente_codigo", "client_code", "customer_code", "sigla_cliente"),
        "customer_name": _first(data, "customer_name", "cliente_nome", "cliente", "nome_cliente"),
        "notes": _first(data, "notes", "observacao", "observações", "obs"),
    })
    return base


def _professional_values(company_id: int, module_code: str, sync_source: str, data: dict[str, Any]):
    base = _base_fields(company_id, module_code, sync_source, data)
    if not base:
        return None
    base.update({
        "name": str(_first(data, "name", "nome", "professional_name", "profissional", default="Profissional sem nome")),
        "phone": _first(data, "phone", "telefone", "celular", "whatsapp"),
        "email": _first(data, "email", "e_mail"),
        "specialty": _first(data, "specialty", "especialidade", "funcao", "função"),
        "notes": _first(data, "notes", "observacao", "observações", "obs"),
    })
    return base


def _service_values(company_id: int, module_code: str, sync_source: str, data: dict[str, Any]):
    base = _base_fields(company_id, module_code, sync_source, data)
    if not base:
        return None
    duration = _first(data, "duration_minutes", "duration", "duracao", "duração", "tempo")
    try:
        duration = int(duration) if duration not in (None, "") else None
    except Exception:
        duration = None
    base.update({
        "name": str(_first(data, "name", "nome", "service_name", "servico", "serviço", default="Serviço sem nome")),
        "price": _amount(_first(data, "price", "preco", "preço", "valor", "amount")),
        "duration_minutes": duration,
        "category": _first(data, "category", "categoria", "grupo"),
        "notes": _first(data, "notes", "observacao", "observações", "obs"),
    })
    return base


def _looks_like_studio_customer_code(value: Any) -> bool:
    return bool(__import__("re").fullmatch(r"STR\d{4}", str(value or "").strip(), flags=__import__("re").IGNORECASE))


def _payload_dict(record) -> dict[str, Any]:
    try:
        value = json.loads(getattr(record, "raw_payload", None) or "{}")
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _norm_text(value: Any) -> str:
    return " ".join(str(value or "").strip().casefold().split())


def _norm_phone(value: Any) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if digits.startswith("55") and len(digits) > 11:
        digits = digits[2:]
    return digits[-11:]


def _customer_reconcile_score(record: Customer, incoming_raw: dict[str, Any], values: dict[str, Any]) -> int:
    """Pontua somente vínculos suficientemente fortes para migrar CLI-X -> STRxxxx."""
    target = str(values.get("external_id") or "").strip().upper()
    if not _looks_like_studio_customer_code(target):
        return 0
    current_external = str(record.external_id or "").strip()
    if not _looks_like_generated_client_code(current_external):
        return 0

    incoming_legacy = _first(incoming_raw, "external_id", "externalId", "api_external_id")
    if incoming_legacy and _looks_like_generated_client_code(incoming_legacy):
        if current_external.upper() == str(incoming_legacy).strip().upper():
            return 1000

    raw = _payload_dict(record)
    raw_code = _customer_code(raw)
    if raw_code and str(raw_code).strip().upper() == target:
        return 950

    incoming_document = _norm_text(values.get("document"))
    existing_document = _norm_text(record.document)
    if incoming_document and existing_document and incoming_document == existing_document:
        return 900

    incoming_email = _norm_text(values.get("email"))
    existing_email = _norm_text(record.email)
    incoming_name = _norm_text(values.get("name"))
    existing_name = _norm_text(record.name)
    if incoming_email and existing_email and incoming_email == existing_email and incoming_name == existing_name:
        return 850

    incoming_phone = _norm_phone(values.get("phone"))
    existing_phone = _norm_phone(record.phone)
    if incoming_phone and existing_phone and incoming_phone == existing_phone and incoming_name == existing_name:
        return 800
    return 0


def _find_legacy_customer(db: Session, incoming_raw: dict[str, Any], values: dict[str, Any], *, exclude_id: int | None = None) -> Customer | None:
    target = str(values.get("external_id") or "").strip()
    if not _looks_like_studio_customer_code(target):
        return None
    query = db.query(Customer).filter(
        Customer.company_id == values["company_id"],
        Customer.module_code == values["module_code"],
        Customer.external_id != target,
        Customer.is_deleted == False,  # noqa: E712
    )
    if exclude_id is not None:
        query = query.filter(Customer.id != exclude_id)
    scored: list[tuple[int, Customer]] = []
    for candidate in query.all():
        score = _customer_reconcile_score(candidate, incoming_raw, values)
        if score > 0:
            scored.append((score, candidate))
    if not scored:
        return None
    scored.sort(key=lambda pair: pair[0], reverse=True)
    # Empate na maior pontuação = não arriscar mesclar pessoas diferentes.
    if len(scored) > 1 and scored[0][0] == scored[1][0]:
        return None
    return scored[0][1]


def _repoint_customer_references(db: Session, company_id: int, old_external: str, new_external: str) -> None:
    if not old_external or old_external == new_external:
        return
    for record in db.query(Appointment).filter(
        Appointment.company_id == company_id,
        Appointment.customer_external_id == old_external,
    ).all():
        record.customer_external_id = new_external
        raw = _payload_dict(record)
        for key in ("customer_external_id", "client_uid", "client_code", "customer_code", "codigo_cliente", "cliente_codigo", "sigla_cliente"):
            if str(raw.get(key) or "").strip() == old_external:
                raw[key] = new_external
        record.raw_payload = json.dumps(raw, ensure_ascii=False, default=str)
    for record in db.query(TransactionRecord).filter(
        TransactionRecord.company_id == company_id,
        TransactionRecord.customer_external_id == old_external,
    ).all():
        record.customer_external_id = new_external
        raw = _payload_dict(record)
        for key in ("customer_external_id", "client_uid", "client_code", "customer_code", "codigo_cliente", "cliente_codigo", "sigla_cliente"):
            if str(raw.get(key) or "").strip() == old_external:
                raw[key] = new_external
        record.raw_payload = json.dumps(raw, ensure_ascii=False, default=str)


def _attach_legacy_customer_id(record: Customer, legacy_external: str, target_external: str) -> None:
    raw = _payload_dict(record)
    aliases = raw.get("legacy_external_ids")
    if not isinstance(aliases, list):
        aliases = []
    if legacy_external and legacy_external not in aliases:
        aliases.append(legacy_external)
    raw["legacy_external_ids"] = aliases
    raw["legacy_external_id"] = legacy_external or raw.get("legacy_external_id")
    raw = _with_customer_code_aliases(raw, target_external)
    raw["external_id"] = target_external
    record.raw_payload = json.dumps(raw, ensure_ascii=False, default=str)


def _soft_merge_legacy_customer(db: Session, legacy: Customer, target: Customer) -> None:
    old_external = str(legacy.external_id or "").strip()
    new_external = str(target.external_id or "").strip()
    _repoint_customer_references(db, target.company_id, old_external, new_external)
    _attach_legacy_customer_id(target, old_external, new_external)
    raw = _payload_dict(legacy)
    raw.update({
        "merged": True,
        "merged_into_id": target.id,
        "merged_into_external_id": new_external,
        "legacy_external_id": old_external,
    })
    legacy.raw_payload = json.dumps(raw, ensure_ascii=False, default=str)
    legacy.is_deleted = True
    legacy.deleted_at = datetime.now(timezone.utc)
    legacy.sync_source = "core_reconciled"


def reconcile_existing_customer_codes(db: Session, *, company_id: int | None = None) -> dict[str, int]:
    """Concilia duplicatas já existentes STRxxxx + CLI-X de forma conservadora."""
    stats = {"scanned": 0, "merged": 0, "migrated": 0, "ignored": 0}
    query = db.query(Customer).filter(Customer.is_deleted == False)  # noqa: E712
    if company_id is not None:
        query = query.filter(Customer.company_id == company_id)
    records = query.order_by(Customer.id.asc()).all()
    for record in records:
        if record.is_deleted:
            continue
        stats["scanned"] += 1
        raw = _payload_dict(record)
        code = _customer_code(raw)
        if _looks_like_studio_customer_code(code) and _looks_like_generated_client_code(record.external_id):
            values = _customer_values(record.company_id, record.module_code, record.sync_source, {**raw, "external_id": record.external_id, "sigla": code})
            if values:
                existing_target = db.query(Customer).filter(
                    Customer.company_id == record.company_id,
                    Customer.module_code == record.module_code,
                    Customer.external_id == str(code).upper(),
                ).first()
                if existing_target and existing_target.id != record.id:
                    _soft_merge_legacy_customer(db, record, existing_target)
                    stats["merged"] += 1
                elif not existing_target:
                    old_external = record.external_id
                    _repoint_customer_references(db, record.company_id, old_external, str(code).upper())
                    record.external_id = str(code).upper()
                    _attach_legacy_customer_id(record, old_external, record.external_id)
                    stats["migrated"] += 1
                continue
        if _looks_like_studio_customer_code(record.external_id):
            values = _customer_values(record.company_id, record.module_code, record.sync_source, {**raw, "external_id": record.external_id, "sigla": record.external_id, "name": record.name, "phone": record.phone, "email": record.email, "document": record.document})
            if values:
                legacy = _find_legacy_customer(db, raw, values, exclude_id=record.id)
                if legacy:
                    _soft_merge_legacy_customer(db, legacy, record)
                    stats["merged"] += 1
                    continue
        stats["ignored"] += 1
    db.commit()
    return stats


ENTITY_CONFIG = {
    "clients": (Customer, _customer_values, "clientes"),
    "customers": (Customer, _customer_values, "clientes"),
    "appointments": (Appointment, _appointment_values, "agendamentos"),
    "transactions": (TransactionRecord, _transaction_values, "financeiro"),
    "professionals": (Professional, _professional_values, "profissionais"),
    "services": (ServiceCatalog, _service_values, "serviços"),
}


def upsert_items(db: Session, *, entity: str, company_id: int, module_code: str, sync_source: str, items: list[dict[str, Any]]) -> dict[str, int]:
    model, builder, _ = ENTITY_CONFIG[entity]
    stats = {"received": len(items), "created": 0, "updated": 0, "ignored": 0, "errors": 0, "reconciled": 0}

    for raw in items:
        if not isinstance(raw, dict):
            stats["ignored"] += 1
            continue
        try:
            values = builder(company_id, module_code, sync_source, raw)
            if not values:
                stats["ignored"] += 1
                continue
            record = db.query(model).filter(
                model.company_id == values["company_id"],
                model.module_code == values["module_code"],
                model.external_id == values["external_id"],
            ).first()

            # V1.0.1.9: clientes antigos CLI-X/API_CLIENT-X são reconciliados com
            # a STRxxxx do Studio em vez de criar uma segunda pessoa no banco.
            legacy = None
            if entity in {"clients", "customers"} and _looks_like_studio_customer_code(values.get("external_id")):
                legacy = _find_legacy_customer(db, raw, values, exclude_id=getattr(record, "id", None))
                if record is None and legacy is not None:
                    old_external = str(legacy.external_id or "").strip()
                    _repoint_customer_references(db, values["company_id"], old_external, values["external_id"])
                    record = legacy
                    for key, value in values.items():
                        setattr(record, key, value)
                    _attach_legacy_customer_id(record, old_external, values["external_id"])
                    stats["updated"] += 1
                    stats["reconciled"] += 1
                    continue

            if record:
                # V1.0.1.10: um registro que nasceu na Agenda Online mantém sua origem
                # mesmo se for editado/reconfirmado posteriormente pelo Studio.
                if entity in {"clients", "customers", "appointments"} and str(getattr(record, "sync_source", "") or "").lower() == "online_booking" and str(values.get("sync_source") or "").lower() == "desktop_sync":
                    values["sync_source"] = "online_booking"
                    try:
                        payload = json.loads(values.get("raw_payload") or "{}")
                    except Exception:
                        payload = {}
                    if not isinstance(payload, dict):
                        payload = {}
                    payload["source"] = "online_booking"
                    payload["sync_source"] = "online_booking"
                    payload["last_source"] = "desktop_sync"
                    values["raw_payload"] = json.dumps(payload, ensure_ascii=False, default=str)
                for key, value in values.items():
                    setattr(record, key, value)
                if entity in {"clients", "customers"} and legacy is not None and legacy.id != record.id:
                    _soft_merge_legacy_customer(db, legacy, record)
                    stats["reconciled"] += 1
                stats["updated"] += 1
            else:
                db.add(model(**values))
                stats["created"] += 1
        except Exception:
            stats["errors"] += 1
    db.commit()
    return stats


def write_sync_log(db: Session, *, company_id: int, module_code: str, direction: str, status: str, message: str, stats: dict[str, int]) -> SyncLog:
    log = SyncLog(
        company_id=company_id,
        module_code=module_code,
        direction=direction,
        status=status,
        message=message,
        total_received=stats.get("received", 0),
        total_created=stats.get("created", 0),
        total_updated=stats.get("updated", 0),
        total_ignored=stats.get("ignored", 0),
        total_errors=stats.get("errors", 0),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
