from sqlalchemy.orm import Session
from app.models.logs import AuditLog


def write_audit(db: Session, *, company_id=None, user_id=None, module_code=None, action: str, description: str | None = None, ip_address: str | None = None):
    log = AuditLog(
        company_id=company_id,
        user_id=user_id,
        module_code=module_code,
        action=action,
        description=description,
        ip_address=ip_address,
    )
    db.add(log)
    db.commit()
    return log
