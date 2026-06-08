from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.logs import AuditLog
from app.routes.deps import require_master_or_admin
from app.schemas.logs import AuditLogResponse

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/logs", response_model=list[AuditLogResponse])
def list_audit_logs(company_id: int | None = None, module_code: str | None = None, limit: int = 100, db: Session = Depends(get_db), _=Depends(require_master_or_admin)):
    query = db.query(AuditLog)
    if company_id:
        query = query.filter(AuditLog.company_id == company_id)
    if module_code:
        query = query.filter(AuditLog.module_code == module_code)
    return query.order_by(AuditLog.id.desc()).limit(limit).all()
