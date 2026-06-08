from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.session import get_db
from app.models.company import Company
from app.models.module import CompanyModule, Module
from app.models.user import User
from app.models.logs import AuditLog, SyncLog
from app.models.business import Appointment, Customer, TransactionRecord

router = APIRouter(prefix="/api", tags=["status"])


def _database_label(database_url: str) -> str:
    if database_url.startswith("sqlite"):
        return "SQLite local"
    if database_url.startswith("postgresql"):
        return "PostgreSQL"
    return database_url.split(":", 1)[0]


@router.get("/status")
def status(db: Session = Depends(get_db)):
    settings = get_settings()
    db.execute(text("SELECT 1"))
    return {
        "status": "online",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "database": _database_label(settings.database_url),
    }


@router.get("/core/overview")
def core_overview(db: Session = Depends(get_db)):
    settings = get_settings()
    enabled_modules = (
        db.query(CompanyModule)
        .filter(CompanyModule.is_enabled == True)  # noqa: E712
        .count()
    )
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "database": _database_label(settings.database_url),
        "totals": {
            "companies": db.query(Company).count(),
            "users": db.query(User).count(),
            "modules": db.query(Module).count(),
            "enabled_company_modules": enabled_modules,
            "sync_logs": db.query(SyncLog).count(),
            "audit_logs": db.query(AuditLog).count(),
            "clients": db.query(Customer).count(),
            "appointments": db.query(Appointment).count(),
            "transactions": db.query(TransactionRecord).count(),
        },
        "official_standards": "/api/core/official-standards",
        "docs": "/docs",
        "health": "/api/status",
        "default_login": {
            "username": settings.master_username,
            "company_slug": settings.default_company_slug,
        },
    }
