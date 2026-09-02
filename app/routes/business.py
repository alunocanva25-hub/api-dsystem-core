from typing import Any
import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.business import Appointment, Customer, TransactionRecord
from app.routes.deps import get_current_user
from app.schemas.business import AppointmentResponse, CustomerResponse, SyncBatchRequest, SyncBatchResponse
from app.services.sync_service import upsert_items, write_sync_log

router = APIRouter(prefix="/api", tags=["business-sync"])


def _sync_response(*, entity: str, module_code: str, sync_source: str, stats: dict, sync_log_id: int, label: str) -> dict:
    return {
        "ok": stats.get("errors", 0) == 0,
        "entity": entity,
        "module_code": module_code,
        "sync_source": sync_source,
        "total_received": stats.get("received", 0),
        "total_created": stats.get("created", 0),
        "total_updated": stats.get("updated", 0),
        "total_ignored": stats.get("ignored", 0),
        "total_errors": stats.get("errors", 0),
        "sync_log_id": sync_log_id,
        "message": f"Sync de {label} processado.",
    }


def _dt(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _normalize_financial_type(value: Any) -> str:
    """Normaliza o tipo financeiro para o contrato do DS STUDIO GO.

    O GO precisa conseguir calcular:
    Receitas = entrada
    Despesas = saida
    Saldo = entradas - saidas
    """
    txt = str(value or "").strip().lower()
    txt = txt.replace("í", "i").replace("é", "e").replace("ê", "e").replace("á", "a").replace("ã", "a").replace("ç", "c")
    income_values = {
        "entrada", "receita", "income", "credit", "credito", "in", "positivo", "+", "e", "receber", "a receber"
    }
    expense_values = {
        "saida", "despesa", "expense", "debit", "debito", "out", "negativo", "-", "s", "pagar", "a pagar"
    }
    if txt in income_values:
        return "entrada"
    if txt in expense_values:
        return "saida"
    return txt or "entrada"


def _transaction_out(t: TransactionRecord) -> dict[str, Any]:
    raw = {}
    try:
        raw = json.loads(t.raw_payload or "{}")
    except Exception:
        raw = {}
    kind = _normalize_financial_type(t.transaction_type)
    amount = float(t.amount or 0)
    occurred_at = t.transaction_date
    return {
        "id": t.id,
        "company_id": t.company_id,
        "module_code": t.module_code,
        "external_id": t.external_id,
        "source": t.sync_source,
        "sync_source": t.sync_source,
        "last_source": raw.get("last_source") or t.sync_source,
        "status": raw.get("status") or ("cancelado" if t.is_deleted else None),
        "sync_status": raw.get("sync_status") or ("cancelado" if t.is_deleted else None),
        "desktop_imported": raw.get("desktop_imported", False),
        "pending_desktop_pull": raw.get("pending_desktop_pull", bool(t.is_deleted and (t.sync_source == "go_mobile"))),

        # Contrato financeiro compatível com GO antigo/novo
        "kind": kind,
        "type": kind,
        "tipo": kind,
        "transaction_type": kind,
        "natureza": kind,

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

        "customer_external_id": t.customer_external_id,
        "client_uid": t.customer_external_id,
        "customer_name": t.customer_name,
        "client_name": t.customer_name,
        "notes": t.notes,

        "deleted": bool(t.is_deleted),
        "is_deleted": bool(t.is_deleted),
        "deleted_at": _dt(t.deleted_at),
        "created_at": _dt(t.created_at),
        "updated_at": _dt(t.updated_at),
    }


def _financial_summary(records: list[TransactionRecord]) -> dict[str, Any]:
    receitas = 0.0
    despesas = 0.0
    total = 0
    for record in records:
        if bool(record.is_deleted):
            continue
        amount = float(record.amount or 0)
        kind = _normalize_financial_type(record.transaction_type)
        if kind == "saida":
            despesas += amount
        else:
            receitas += amount
        total += 1
    saldo = receitas - despesas
    return {
        "receitas": receitas,
        "despesas": despesas,
        "saldo": saldo,
        "income": receitas,
        "expenses": despesas,
        "balance": saldo,
        "total_transactions": total,
    }


@router.post("/sync/clients", response_model=SyncBatchResponse)
def sync_clients(payload: SyncBatchRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    stats = upsert_items(db, entity="clients", company_id=current_user.company_id, module_code=payload.module_code, sync_source=payload.sync_source, items=payload.items)
    log = write_sync_log(db, company_id=current_user.company_id, module_code=payload.module_code, direction="desktop_to_api", status="success" if stats["errors"] == 0 else "warning", message="Sync de clientes", stats=stats)
    return _sync_response(entity="clients", module_code=payload.module_code, sync_source=payload.sync_source, stats=stats, sync_log_id=log.id, label="clientes")


@router.get("/clients", response_model=list[CustomerResponse])
def list_clients(module_code: str | None = None, source: str | None = None, include_deleted: bool = False, limit: int = 200, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(Customer).filter(Customer.company_id == current_user.company_id)
    if module_code:
        query = query.filter(Customer.module_code == module_code)
    if source:
        query = query.filter(Customer.sync_source == source)
    if not include_deleted:
        query = query.filter(Customer.is_deleted == False)  # noqa: E712
    return query.order_by(Customer.name).limit(limit).all()


@router.post("/sync/appointments", response_model=SyncBatchResponse)
def sync_appointments(payload: SyncBatchRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    stats = upsert_items(db, entity="appointments", company_id=current_user.company_id, module_code=payload.module_code, sync_source=payload.sync_source, items=payload.items)
    log = write_sync_log(db, company_id=current_user.company_id, module_code=payload.module_code, direction="desktop_to_api", status="success" if stats["errors"] == 0 else "warning", message="Sync de agendamentos", stats=stats)
    return _sync_response(entity="appointments", module_code=payload.module_code, sync_source=payload.sync_source, stats=stats, sync_log_id=log.id, label="agendamentos")


@router.get("/appointments", response_model=list[AppointmentResponse])
def list_appointments(module_code: str | None = None, source: str | None = None, include_deleted: bool = False, limit: int = 200, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(Appointment).filter(Appointment.company_id == current_user.company_id)
    if module_code:
        query = query.filter(Appointment.module_code == module_code)
    if source:
        query = query.filter(Appointment.sync_source == source)
    if not include_deleted:
        query = query.filter(Appointment.is_deleted == False)  # noqa: E712
    return query.order_by(Appointment.start_at.desc()).limit(limit).all()


@router.post("/sync/transactions", response_model=SyncBatchResponse)
def sync_transactions(payload: SyncBatchRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    stats = upsert_items(db, entity="transactions", company_id=current_user.company_id, module_code=payload.module_code, sync_source=payload.sync_source, items=payload.items)
    log = write_sync_log(db, company_id=current_user.company_id, module_code=payload.module_code, direction="desktop_to_api", status="success" if stats["errors"] == 0 else "warning", message="Sync financeiro", stats=stats)
    return _sync_response(entity="transactions", module_code=payload.module_code, sync_source=payload.sync_source, stats=stats, sync_log_id=log.id, label="financeiro")


@router.get("/transactions")
def list_transactions(module_code: str | None = None, source: str | None = None, include_deleted: bool = False, limit: int = 500, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(TransactionRecord).filter(TransactionRecord.company_id == current_user.company_id)
    if module_code:
        query = query.filter(TransactionRecord.module_code == module_code)
    if source:
        query = query.filter(TransactionRecord.sync_source == source)
    if not include_deleted:
        query = query.filter(TransactionRecord.is_deleted == False)  # noqa: E712
    records = query.order_by(TransactionRecord.transaction_date.desc()).limit(limit).all()
    return [_transaction_out(x) for x in records]


@router.get("/transactions/summary")
def transactions_summary(module_code: str | None = None, source: str | None = None, include_deleted: bool = False, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(TransactionRecord).filter(TransactionRecord.company_id == current_user.company_id)
    if module_code:
        query = query.filter(TransactionRecord.module_code == module_code)
    if source:
        query = query.filter(TransactionRecord.sync_source == source)
    if not include_deleted:
        query = query.filter(TransactionRecord.is_deleted == False)  # noqa: E712
    return _financial_summary(query.all())


@router.get("/financial/summary")
def financial_summary(module_code: str | None = None, source: str | None = None, include_deleted: bool = False, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(TransactionRecord).filter(TransactionRecord.company_id == current_user.company_id)
    if module_code:
        query = query.filter(TransactionRecord.module_code == module_code)
    if source:
        query = query.filter(TransactionRecord.sync_source == source)
    if not include_deleted:
        query = query.filter(TransactionRecord.is_deleted == False)  # noqa: E712
    return _financial_summary(query.all())
