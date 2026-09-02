from sqlalchemy.orm import Session
from app.models.company import Company
from app.models.module import CompanyModule, Module
from app.services.permission_service import build_permissions


def get_enabled_modules_for_company(db: Session, company_id: int) -> list[dict]:
    """Retorna módulos ativos/liberados para uma empresa.

    Usado no login, /me e nos clientes mobile/desktop para saber quais áreas
    do ecossistema DSYSTEM podem aparecer na interface.
    """
    rows = (
        db.query(CompanyModule, Module)
        .join(Module, Module.id == CompanyModule.module_id)
        .filter(
            CompanyModule.company_id == company_id,
            CompanyModule.is_enabled == True,  # noqa: E712
            Module.is_active == True,  # noqa: E712
        )
        .order_by(Module.name)
        .all()
    )
    return [
        {
            "id": module.id,
            "code": module.code,
            "name": module.name,
            "description": module.description,
            "plan": link.plan,
            "is_enabled": link.is_enabled,
        }
        for link, module in rows
    ]


def get_company_context(db: Session, company_id: int) -> dict | None:
    company = db.get(Company, company_id)
    if not company:
        return None
    return {
        "id": company.id,
        "name": company.name,
        "slug": company.slug,
        "document": company.document,
        "is_active": company.is_active,
    }


def build_user_session(db: Session, user) -> dict:
    company = get_company_context(db, user.company_id)
    modules = get_enabled_modules_for_company(db, user.company_id)
    permissions = build_permissions(user.role, modules)
    return {
        "id": user.id,
        "company_id": user.company_id,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "company": company,
        "modules": modules,
        "permissions": permissions,
    }
