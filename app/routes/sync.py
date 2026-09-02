from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.logs import SyncLog
from app.routes.deps import get_current_user, require_master_or_admin
from app.schemas.logs import SyncLogCreate, SyncLogResponse
from app.services.sync_service import upsert_items, write_sync_log

router = APIRouter(prefix="/api/sync", tags=["sync"])


def _extract_items(payload: dict, *names: str) -> list[dict]:
    for name in names:
        value = payload.get(name)
        if isinstance(value, list):
            return value
    return []


@router.get("/ping")
def sync_ping(current_user=Depends(get_current_user)):
    return {
        "ok": True,
        "message": "Canal de sincronização disponível",
        "server_time": datetime.now(timezone.utc).isoformat(),
        "company_id": current_user.company_id,
        "user": current_user.username,
    }


@router.post("/logs", response_model=SyncLogResponse)
def create_sync_log(payload: SyncLogCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    log = SyncLog(**payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/logs", response_model=list[SyncLogResponse])
def list_sync_logs(company_id: int | None = None, module_code: str | None = None, limit: int = 100, db: Session = Depends(get_db), _=Depends(require_master_or_admin)):
    query = db.query(SyncLog)
    if company_id:
        query = query.filter(SyncLog.company_id == company_id)
    if module_code:
        query = query.filter(SyncLog.module_code == module_code)
    return query.order_by(SyncLog.id.desc()).limit(limit).all()


@router.post("/studio")
def receive_studio_sync(payload: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Recebe um pacote geral do DSYSTEM STUDIO Desktop.

    Aceita chaves: clients/customers, appointments e transactions.
    Cada item precisa ter algum identificador local: external_id, local_id ou id.
    """
    module_code = str(payload.get("module_code") or "studio") if isinstance(payload, dict) else "studio"
    sync_source = str(payload.get("sync_source") or "desktop_sync") if isinstance(payload, dict) else "desktop_sync"

    clients = _extract_items(payload, "clients", "customers", "clientes") if isinstance(payload, dict) else []
    appointments = _extract_items(payload, "appointments", "agendamentos") if isinstance(payload, dict) else []
    transactions = _extract_items(payload, "transactions", "financeiro", "lancamentos", "lançamentos") if isinstance(payload, dict) else []

    stats_clients = upsert_items(db, entity="clients", company_id=current_user.company_id, module_code=module_code, sync_source=sync_source, items=clients)
    stats_appointments = upsert_items(db, entity="appointments", company_id=current_user.company_id, module_code=module_code, sync_source=sync_source, items=appointments)
    stats_transactions = upsert_items(db, entity="transactions", company_id=current_user.company_id, module_code=module_code, sync_source=sync_source, items=transactions)

    totals = {
        "received": stats_clients["received"] + stats_appointments["received"] + stats_transactions["received"],
        "created": stats_clients["created"] + stats_appointments["created"] + stats_transactions["created"],
        "updated": stats_clients["updated"] + stats_appointments["updated"] + stats_transactions["updated"],
        "ignored": stats_clients["ignored"] + stats_appointments["ignored"] + stats_transactions["ignored"],
        "errors": stats_clients["errors"] + stats_appointments["errors"] + stats_transactions["errors"],
    }
    log = write_sync_log(
        db,
        company_id=current_user.company_id,
        module_code=module_code,
        direction="desktop_to_api",
        status="success" if totals["errors"] == 0 else "warning",
        message="Pacote geral do DSYSTEM STUDIO processado",
        stats=totals,
    )
    return {
        "ok": totals["errors"] == 0,
        "module_code": module_code,
        "sync_source": sync_source,
        "sync_log_id": log.id,
        "totals": {
            "total_received": totals["received"],
            "total_created": totals["created"],
            "total_updated": totals["updated"],
            "total_ignored": totals["ignored"],
            "total_errors": totals["errors"],
        },
        "details": {
            "clients": stats_clients,
            "appointments": stats_appointments,
            "transactions": stats_transactions,
        },
        "message": "Payload do Studio processado com upsert por company_id + module_code + external_id.",
    }
