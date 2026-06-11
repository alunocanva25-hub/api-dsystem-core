from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.business import Appointment, Customer, Professional, ServiceCatalog, TransactionRecord
from app.models.user import User
from app.routes.deps import get_current_user
from app.services.sync_service import upsert_items

router = APIRouter(prefix="/api", tags=["go-compat-complete"])


def _dt(value):
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _raw(record) -> dict[str, Any]:
    try:
        return json.loads(record.raw_payload or "{}")
    except Exception:
        return {}


def _is_deleted_from_payload(data: dict[str, Any], current: bool = False) -> bool:
    status_value = data.get("sync_status") or data.get("status") or data.get("situacao") or data.get("situação") or ""
    status_txt = str(status_value).strip().lower()
    status_txt = status_txt.replace("í", "i").replace("é", "e").replace("ê", "e").replace("á", "a").replace("ã", "a").replace("ç", "c")
    status_deleted = status_txt in {"cancelado", "cancelada", "cancelled", "canceled", "excluido", "excluida", "deleted", "removido", "removida"}
    if "is_active" in data:
        return (not bool(data.get("is_active"))) or status_deleted
    value = data.get("is_deleted", data.get("deleted", current))
    if isinstance(value, bool):
        return value or status_deleted
    if isinstance(value, (int, float)):
        return bool(value) or status_deleted
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "sim", "s", "yes", "deleted", "excluido", "excluida", "cancelado", "cancelada", "cancelled", "canceled"} or status_deleted
    return bool(value) or status_deleted


def _mark_deleted(record, data: dict[str, Any]):
    old_deleted = bool(getattr(record, "is_deleted", False))
    deleted = _is_deleted_from_payload(data, old_deleted)
    record.is_deleted = deleted
    if deleted and not getattr(record, "deleted_at", None):
        record.deleted_at = datetime.now(timezone.utc)
    if not deleted:
        record.deleted_at = None
        return

    # Contrato oficial GO → API → STUDIO:
    # exclusão lógica feita no GO deve voltar no pull do Studio como cancelamento.
    if hasattr(record, "sync_source"):
        record.sync_source = data.get("source") or data.get("sync_source") or "go_mobile"
    raw = _raw(record)
    deleted_at_text = _dt(getattr(record, "deleted_at", None))
    raw.update(data)
    raw.update({
        "deleted": True,
        "is_deleted": True,
        "deleted_at": data.get("deleted_at") or deleted_at_text,
        "status": data.get("status") or "cancelado",
        "sync_status": data.get("sync_status") or "cancelado",
        "source": data.get("source") or data.get("sync_source") or "go_mobile",
        "sync_source": data.get("sync_source") or data.get("source") or "go_mobile",
        "last_source": data.get("last_source") or data.get("source") or data.get("sync_source") or "go_mobile",
        "desktop_imported": False,
        "pending_desktop_pull": True,
        "imported": False,
    })
    record.raw_payload = json.dumps(raw, ensure_ascii=False, default=str)


def _client_out(c: Customer) -> dict[str, Any]:
    raw = _raw(c)
    return {
        "id": c.id,
        "external_id": c.external_id,
        "source": c.sync_source or raw.get("source") or "api_local",
        "sync_source": c.sync_source,
        "name": c.name,
        "nome": c.name,
        "phone": c.phone,
        "telefone": c.phone,
        "email": c.email,
        "document": c.document,
        "notes": c.notes,
        "is_active": not bool(c.is_deleted),
        "deleted": bool(c.is_deleted),
        "is_deleted": bool(c.is_deleted),
        "deleted_at": _dt(c.deleted_at),
        "created_at": _dt(c.created_at),
        "updated_at": _dt(c.updated_at),
    }


def _appointment_out(a: Appointment) -> dict[str, Any]:
    raw = _raw(a)
    return {
        "id": a.id,
        "external_id": a.external_id,
        "client_uid": raw.get("client_uid") or a.customer_external_id,
        "source": a.sync_source or raw.get("source") or "api_local",
        "sync_source": a.sync_source,
        "last_source": raw.get("last_source") or a.sync_source,
        "status": raw.get("status") or a.status or ("cancelado" if a.is_deleted else None),
        "sync_status": raw.get("sync_status") or ("cancelado" if a.is_deleted else None),
        "desktop_imported": raw.get("desktop_imported", False),
        "pending_desktop_pull": raw.get("pending_desktop_pull", bool(a.is_deleted and (a.sync_source == "go_mobile"))),
        "client_name": a.customer_name,
        "professional_name": a.professional_name,
        "service_name": a.service_name,
        "phone": raw.get("phone"),
        "notes": a.notes,
        "start_at": a.start_at,
        "end_at": a.end_at,
        "deleted": bool(a.is_deleted),
        "is_deleted": bool(a.is_deleted),
        "deleted_at": _dt(a.deleted_at),
        "created_at": _dt(a.created_at),
        "updated_at": _dt(a.updated_at),
    }


def _normalize_financial_type(value: Any) -> str:
    txt = str(value or "").strip().lower()
    txt = txt.replace("í", "i").replace("é", "e").replace("ê", "e").replace("á", "a").replace("ã", "a").replace("ç", "c")
    if txt in {"entrada", "receita", "income", "credit", "credito", "in", "positivo", "+", "e"}:
        return "entrada"
    if txt in {"saida", "despesa", "expense", "debit", "debito", "out", "negativo", "-", "s"}:
        return "saida"
    return txt or "entrada"


def _transaction_out(t: TransactionRecord) -> dict[str, Any]:
    raw = _raw(t)
    kind = _normalize_financial_type(t.transaction_type)
    amount = float(t.amount or 0)
    occurred_at = t.transaction_date
    return {
        "id": t.id,
        "external_id": t.external_id,
        "client_uid": raw.get("client_uid") or t.customer_external_id,
        "source": t.sync_source or raw.get("source") or "api_local",
        "sync_source": t.sync_source,
        "last_source": raw.get("last_source") or t.sync_source,
        "status": raw.get("status") or ("cancelado" if t.is_deleted else None),
        "sync_status": raw.get("sync_status") or ("cancelado" if t.is_deleted else None),
        "desktop_imported": raw.get("desktop_imported", False),
        "pending_desktop_pull": raw.get("pending_desktop_pull", bool(t.is_deleted and (t.sync_source == "go_mobile"))),
        "kind": kind,
        "type": kind,
        "tipo": kind,
        "transaction_type": kind,
        "amount": amount,
        "value": amount,
        "valor": amount,
        "total": amount,
        "category": t.category,
        "categoria": t.category,
        "payment_method": t.payment_method,
        "forma_pagamento": t.payment_method,
        "description": t.description,
        "descricao": t.description,
        "occurred_at": occurred_at,
        "date": occurred_at,
        "data": occurred_at,
        "transaction_date": occurred_at,
        "customer_name": t.customer_name,
        "client_name": t.customer_name,
        "deleted": bool(t.is_deleted),
        "is_deleted": bool(t.is_deleted),
        "deleted_at": _dt(t.deleted_at),
        "created_at": _dt(t.created_at),
        "updated_at": _dt(t.updated_at),
    }


def _professional_out(p: Professional) -> dict[str, Any]:
    raw = _raw(p)
    return {
        "id": p.id,
        "external_id": p.external_id,
        "source": p.sync_source or raw.get("source") or "api_local",
        "sync_source": p.sync_source,
        "name": p.name,
        "nome": p.name,
        "phone": p.phone,
        "email": p.email,
        "specialty": p.specialty,
        "notes": p.notes,
        "is_active": not bool(p.is_deleted),
        "deleted": bool(p.is_deleted),
        "is_deleted": bool(p.is_deleted),
        "deleted_at": _dt(p.deleted_at),
        "created_at": _dt(p.created_at),
        "updated_at": _dt(p.updated_at),
    }


def _service_out(s: ServiceCatalog) -> dict[str, Any]:
    raw = _raw(s)
    return {
        "id": s.id,
        "external_id": s.external_id,
        "source": s.sync_source or raw.get("source") or "api_local",
        "sync_source": s.sync_source,
        "name": s.name,
        "nome": s.name,
        "price": s.price,
        "preco": s.price,
        "duration_minutes": s.duration_minutes,
        "category": s.category,
        "notes": s.notes,
        "is_active": not bool(s.is_deleted),
        "deleted": bool(s.is_deleted),
        "is_deleted": bool(s.is_deleted),
        "deleted_at": _dt(s.deleted_at),
        "created_at": _dt(s.created_at),
        "updated_at": _dt(s.updated_at),
    }


def _query_list(db: Session, model, user: User, source: str | None, include_deleted: bool, limit: int):
    q = db.query(model).filter(model.company_id == user.company_id)
    if source:
        q = q.filter(model.sync_source == source)
    if not include_deleted:
        q = q.filter(model.is_deleted == False)  # noqa: E712
    return q.order_by(model.updated_at.desc()).limit(limit).all()


@router.get("/professionals")
def list_professionals(source: str | None = None, include_deleted: bool = False, limit: int = 500, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return [_professional_out(x) for x in _query_list(db, Professional, current_user, source, include_deleted, limit)]


@router.post("/professionals")
def create_professional(payload: dict[str, Any], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = {**payload, "source": payload.get("source") or "api_local"}
    if not item.get("external_id"):
        item["external_id"] = f"api_prof_{int(datetime.now(timezone.utc).timestamp()*1000)}"
    stats = upsert_items(db, entity="professionals", company_id=current_user.company_id, module_code="studio", sync_source=item.get("source") or "api_local", items=[item])
    return {"ok": stats["errors"] == 0, "message": "Profissional salvo", **stats}


@router.put("/professionals/{item_id}")
@router.patch("/professionals/{item_id}")
def update_professional(item_id: int, payload: dict[str, Any], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = db.query(Professional).filter(Professional.id == item_id, Professional.company_id == current_user.company_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    record.name = payload.get("name") or payload.get("nome") or record.name
    record.phone = payload.get("phone") or payload.get("telefone") or record.phone
    record.email = payload.get("email", record.email)
    record.specialty = payload.get("specialty") or payload.get("especialidade") or record.specialty
    record.notes = payload.get("notes") or payload.get("observacao") or record.notes
    record.sync_source = payload.get("source") or payload.get("sync_source") or record.sync_source
    record.raw_payload = json.dumps({**_raw(record), **payload}, ensure_ascii=False, default=str)
    _mark_deleted(record, payload)
    db.commit(); db.refresh(record)
    return _professional_out(record)


@router.get("/services")
def list_services(source: str | None = None, include_deleted: bool = False, limit: int = 500, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return [_service_out(x) for x in _query_list(db, ServiceCatalog, current_user, source, include_deleted, limit)]


@router.post("/services")
def create_service(payload: dict[str, Any], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = {**payload, "source": payload.get("source") or "api_local"}
    if not item.get("external_id"):
        item["external_id"] = f"api_service_{int(datetime.now(timezone.utc).timestamp()*1000)}"
    stats = upsert_items(db, entity="services", company_id=current_user.company_id, module_code="studio", sync_source=item.get("source") or "api_local", items=[item])
    return {"ok": stats["errors"] == 0, "message": "Serviço salvo", **stats}


@router.put("/services/{item_id}")
@router.patch("/services/{item_id}")
def update_service(item_id: int, payload: dict[str, Any], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = db.query(ServiceCatalog).filter(ServiceCatalog.id == item_id, ServiceCatalog.company_id == current_user.company_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    record.name = payload.get("name") or payload.get("nome") or record.name
    if "price" in payload or "preco" in payload or "valor" in payload:
        value = payload.get("price", payload.get("preco", payload.get("valor", record.price)))
        try:
            record.price = float(str(value).replace("R$", "").replace(".", "").replace(",", "."))
        except Exception:
            pass
    if "duration_minutes" in payload or "duration" in payload or "duracao" in payload:
        try:
            record.duration_minutes = int(payload.get("duration_minutes", payload.get("duration", payload.get("duracao"))))
        except Exception:
            pass
    record.category = payload.get("category") or payload.get("categoria") or record.category
    record.notes = payload.get("notes") or payload.get("observacao") or record.notes
    record.sync_source = payload.get("source") or payload.get("sync_source") or record.sync_source
    record.raw_payload = json.dumps({**_raw(record), **payload}, ensure_ascii=False, default=str)
    _mark_deleted(record, payload)
    db.commit(); db.refresh(record)
    return _service_out(record)


@router.post("/clients")
def create_client_fallback(payload: dict[str, Any], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = {**payload, "source": payload.get("source") or "api_local"}
    if not item.get("external_id"):
        item["external_id"] = f"api_client_{int(datetime.now(timezone.utc).timestamp()*1000)}"
    stats = upsert_items(db, entity="clients", company_id=current_user.company_id, module_code="studio", sync_source=item.get("source") or "api_local", items=[item])
    return {"ok": stats["errors"] == 0, "message": "Cliente salvo", **stats}


def _get_record_or_404(db: Session, model, item_id: int, current_user: User):
    record = db.query(model).filter(model.id == item_id, model.company_id == current_user.company_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    return record


@router.put("/clients/{item_id}")
@router.patch("/clients/{item_id}")
def update_client(item_id: int, payload: dict[str, Any], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = _get_record_or_404(db, Customer, item_id, current_user)
    record.name = payload.get("name") or payload.get("nome") or record.name
    record.phone = payload.get("phone") or payload.get("telefone") or payload.get("celular") or record.phone
    record.email = payload.get("email", record.email)
    record.document = payload.get("document") or payload.get("cpf") or payload.get("cnpj") or record.document
    record.notes = payload.get("notes") or payload.get("observacao") or record.notes
    record.sync_source = payload.get("source") or payload.get("sync_source") or record.sync_source
    record.raw_payload = json.dumps({**_raw(record), **payload}, ensure_ascii=False, default=str)
    _mark_deleted(record, payload)
    db.commit(); db.refresh(record)
    return _client_out(record)


@router.delete("/clients/{item_id}")
def delete_client(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = _get_record_or_404(db, Customer, item_id, current_user)
    _mark_deleted(record, {"deleted": True, "source": "go_mobile", "sync_status": "cancelado", "status": "cancelado"})
    db.commit(); db.refresh(record)
    return _client_out(record)


@router.put("/appointments/{item_id}")
@router.patch("/appointments/{item_id}")
def update_appointment(item_id: int, payload: dict[str, Any], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = _get_record_or_404(db, Appointment, item_id, current_user)
    record.customer_name = payload.get("client_name") or payload.get("customer_name") or payload.get("cliente") or record.customer_name
    record.professional_name = payload.get("professional_name") or payload.get("profissional") or record.professional_name
    record.service_name = payload.get("service_name") or payload.get("servico") or record.service_name
    record.start_at = payload.get("start_at") or payload.get("inicio") or record.start_at
    record.end_at = payload.get("end_at") or payload.get("fim") or record.end_at
    record.status = payload.get("status", record.status)
    record.notes = payload.get("notes") or payload.get("observacao") or record.notes
    record.sync_source = payload.get("source") or payload.get("sync_source") or record.sync_source
    record.raw_payload = json.dumps({**_raw(record), **payload}, ensure_ascii=False, default=str)
    _mark_deleted(record, payload)
    db.commit(); db.refresh(record)
    return _appointment_out(record)


@router.delete("/appointments/{item_id}")
def delete_appointment(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = _get_record_or_404(db, Appointment, item_id, current_user)
    _mark_deleted(record, {"deleted": True, "source": "go_mobile", "sync_status": "cancelado", "status": "cancelado"})
    db.commit(); db.refresh(record)
    return _appointment_out(record)


@router.put("/transactions/{item_id}")
@router.patch("/transactions/{item_id}")
def update_transaction(item_id: int, payload: dict[str, Any], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = _get_record_or_404(db, TransactionRecord, item_id, current_user)
    record.description = payload.get("description") or payload.get("descricao") or record.description
    if "amount" in payload or "valor" in payload:
        value = payload.get("amount", payload.get("valor"))
        try:
            record.amount = float(str(value).replace("R$", "").replace(".", "").replace(",", "."))
        except Exception:
            pass
    record.transaction_type = payload.get("kind") or payload.get("type") or payload.get("transaction_type") or record.transaction_type
    record.category = payload.get("category") or payload.get("categoria") or record.category
    record.payment_method = payload.get("payment_method") or payload.get("forma_pagamento") or record.payment_method
    record.transaction_date = payload.get("occurred_at") or payload.get("transaction_date") or payload.get("data") or record.transaction_date
    record.customer_name = payload.get("client_name") or payload.get("customer_name") or record.customer_name
    record.sync_source = payload.get("source") or payload.get("sync_source") or record.sync_source
    record.raw_payload = json.dumps({**_raw(record), **payload}, ensure_ascii=False, default=str)
    _mark_deleted(record, payload)
    db.commit(); db.refresh(record)
    return _transaction_out(record)


@router.delete("/transactions/{item_id}")
def delete_transaction(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = _get_record_or_404(db, TransactionRecord, item_id, current_user)
    _mark_deleted(record, {"deleted": True, "source": "go_mobile", "sync_status": "cancelado", "status": "cancelado"})
    db.commit(); db.refresh(record)
    return _transaction_out(record)


@router.get("/go/complete-compatibility-map")
def go_complete_compatibility_map():
    return {
        "ok": True,
        "version": "1.0.1.1",
        "compatibility": "DS STUDIO GO V4.0.10.4.36.14",
        "added_routes": [
            "GET/POST/PATCH/PUT /api/professionals",
            "GET/POST/PATCH/PUT /api/services",
            "POST/PATCH/PUT /api/clients",
            "PATCH/PUT /api/appointments",
            "PATCH/PUT /api/transactions",
        ],
        "notes": "Complementa a V1.0.1.0 com catálogos e edição/exclusão lógica esperados pelo GO atual.",
    }
