from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.business import Appointment, Customer, TransactionRecord
from app.routes.deps import get_current_user
from app.schemas.business import AppointmentResponse, CustomerResponse, SyncBatchRequest, SyncBatchResponse, TransactionResponse
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


@router.post("/sync/clients", response_model=SyncBatchResponse)
def sync_clients(payload: SyncBatchRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    stats = upsert_items(db, entity="clients", company_id=current_user.company_id, module_code=payload.module_code, sync_source=payload.sync_source, items=payload.items)
    log = write_sync_log(db, company_id=current_user.company_id, module_code=payload.module_code, direction="desktop_to_api", status="success" if stats["errors"] == 0 else "warning", message="Sync de clientes", stats=stats)
    return _sync_response(entity="clients", module_code=payload.module_code, sync_source=payload.sync_source, stats=stats, sync_log_id=log.id, label="clientes")


@router.get("/clients", response_model=list[CustomerResponse])
def list_clients(module_code: str | None = None, include_deleted: bool = False, limit: int = 200, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(Customer).filter(Customer.company_id == current_user.company_id)
    if module_code:
        query = query.filter(Customer.module_code == module_code)
    if not include_deleted:
        query = query.filter(Customer.is_deleted == False)  # noqa: E712
    return query.order_by(Customer.name).limit(limit).all()


@router.post("/sync/appointments", response_model=SyncBatchResponse)
def sync_appointments(payload: SyncBatchRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    stats = upsert_items(db, entity="appointments", company_id=current_user.company_id, module_code=payload.module_code, sync_source=payload.sync_source, items=payload.items)
    log = write_sync_log(db, company_id=current_user.company_id, module_code=payload.module_code, direction="desktop_to_api", status="success" if stats["errors"] == 0 else "warning", message="Sync de agendamentos", stats=stats)
    return _sync_response(entity="appointments", module_code=payload.module_code, sync_source=payload.sync_source, stats=stats, sync_log_id=log.id, label="agendamentos")


@router.get("/appointments", response_model=list[AppointmentResponse])
def list_appointments(module_code: str | None = None, include_deleted: bool = False, limit: int = 200, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(Appointment).filter(Appointment.company_id == current_user.company_id)
    if module_code:
        query = query.filter(Appointment.module_code == module_code)
    if not include_deleted:
        query = query.filter(Appointment.is_deleted == False)  # noqa: E712
    return query.order_by(Appointment.start_at.desc()).limit(limit).all()


@router.post("/sync/transactions", response_model=SyncBatchResponse)
def sync_transactions(payload: SyncBatchRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    stats = upsert_items(db, entity="transactions", company_id=current_user.company_id, module_code=payload.module_code, sync_source=payload.sync_source, items=payload.items)
    log = write_sync_log(db, company_id=current_user.company_id, module_code=payload.module_code, direction="desktop_to_api", status="success" if stats["errors"] == 0 else "warning", message="Sync financeiro", stats=stats)
    return _sync_response(entity="transactions", module_code=payload.module_code, sync_source=payload.sync_source, stats=stats, sync_log_id=log.id, label="financeiro")


@router.get("/transactions", response_model=list[TransactionResponse])
def list_transactions(module_code: str | None = None, include_deleted: bool = False, limit: int = 200, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(TransactionRecord).filter(TransactionRecord.company_id == current_user.company_id)
    if module_code:
        query = query.filter(TransactionRecord.module_code == module_code)
    if not include_deleted:
        query = query.filter(TransactionRecord.is_deleted == False)  # noqa: E712
    return query.order_by(TransactionRecord.transaction_date.desc()).limit(limit).all()
