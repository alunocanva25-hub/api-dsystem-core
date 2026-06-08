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
    value = _first(data, "external_id", "local_id", "id", "codigo", "cod_cliente", "codcliente", "cod_agendamento", "cod_lancamento")
    if value is None or value == "":
        return None
    return str(value)


def _bool_deleted(data: dict[str, Any]) -> bool:
    value = _first(data, "is_deleted", "deleted", "excluido", "excluida", default=False)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "sim", "s", "yes", "y", "excluido", "excluida", "deleted"}
    return False


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
    return {
        "company_id": company_id,
        "module_code": str(_first(data, "module_code", default=module_code) or module_code),
        "external_id": external_id,
        "sync_source": str(_first(data, "sync_source", default=sync_source) or sync_source),
        "is_deleted": _bool_deleted(data),
        "deleted_at": _deleted_at(data),
        "external_created_at": _first(data, "created_at", "dtcriacao", "data_criacao"),
        "external_updated_at": _first(data, "updated_at", "dtalteracao", "data_alteracao"),
        "raw_payload": json.dumps(data, ensure_ascii=False, default=str),
    }


def _customer_values(company_id: int, module_code: str, sync_source: str, data: dict[str, Any]):
    base = _base_fields(company_id, module_code, sync_source, data)
    if not base:
        return None
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
        "customer_external_id": _first(data, "customer_external_id", "cliente_id", "id_cliente", "cod_cliente"),
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
        "customer_external_id": _first(data, "customer_external_id", "cliente_id", "id_cliente", "cod_cliente"),
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
    stats = {"received": len(items), "created": 0, "updated": 0, "ignored": 0, "errors": 0}

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
            if record:
                for key, value in values.items():
                    setattr(record, key, value)
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
