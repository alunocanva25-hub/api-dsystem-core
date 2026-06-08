from typing import Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import get_db
from app.models.company import Company
from app.models.user import User
from app.models.module import Module, CompanyModule
from app.models.logs import AuditLog, SyncLog
from app.models.product_config import Product, Segment, Plan, CompanyProduct, CompanyProductModule
from app.routes.deps import require_master_or_admin
from app.services.audit_service import write_audit
from app.services.module_service import get_enabled_modules_for_company

router = APIRouter(prefix="/api/admin", tags=["admin-hub"])


class CompanyAdminCreate(BaseModel):
    name: str
    slug: str
    document: str | None = None
    is_active: bool = True


class CompanyAdminUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    document: str | None = None
    is_active: bool | None = None


class UserAdminCreate(BaseModel):
    company_id: int
    username: str
    full_name: str
    password: str
    email: EmailStr | None = None
    role: str = "USER"
    is_active: bool = True


class UserAdminUpdate(BaseModel):
    username: str | None = None
    full_name: str | None = None
    password: str | None = None
    email: EmailStr | None = None
    role: str | None = None
    is_active: bool | None = None


class CompanyProductUpsert(BaseModel):
    company_id: int
    product_code: str
    segment_code: str | None = None
    plan_code: str = "STARTER"
    plan_status: str = "ACTIVE"
    trial_starts_at: datetime | None = None
    trial_ends_at: datetime | None = None
    subscription_starts_at: datetime | None = None
    subscription_ends_at: datetime | None = None
    cancelled_at: datetime | None = None
    is_active: bool = True
    settings_json: dict[str, Any] = Field(default_factory=dict)


class CompanyProductPlanUpdate(BaseModel):
    plan_code: str | None = None
    plan_status: str | None = None
    trial_starts_at: datetime | None = None
    trial_ends_at: datetime | None = None
    subscription_starts_at: datetime | None = None
    subscription_ends_at: datetime | None = None
    cancelled_at: datetime | None = None
    is_active: bool | None = None


class CompanyProductModuleUpsert(BaseModel):
    company_id: int
    product_code: str
    module_code: str
    name: str | None = None
    is_enabled: bool = True
    settings_json: dict[str, Any] = Field(default_factory=dict)


class CompanyModuleAdminUpsert(BaseModel):
    company_id: int
    module_code: str
    plan: str = "default"
    is_enabled: bool = True


def _company_dict(company: Company) -> dict[str, Any]:
    return {
        "id": company.id,
        "name": company.name,
        "document": company.document,
        "slug": company.slug,
        "is_active": company.is_active,
        "created_at": company.created_at,
        "updated_at": company.updated_at,
    }


def _user_dict(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "company_id": user.company_id,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


def _company_config(db: Session, company: Company) -> dict[str, Any]:
    products = db.query(CompanyProduct).filter(CompanyProduct.company_id == company.id).order_by(CompanyProduct.product_code).all()
    product_payload = []
    for cp in products:
        product = db.query(Product).filter(Product.code == cp.product_code).first()
        segment = None
        if cp.segment_code:
            segment = db.query(Segment).filter(Segment.product_code == cp.product_code, Segment.code == cp.segment_code).first()
        plan = db.query(Plan).filter(Plan.code == cp.plan_code).first()
        product_modules = db.query(CompanyProductModule).filter(
            CompanyProductModule.company_id == company.id,
            CompanyProductModule.product_code == cp.product_code,
        ).order_by(CompanyProductModule.module_code).all()
        product_payload.append({
            "product": {
                "code": cp.product_code,
                "name": product.name if product else cp.product_code,
                "tagline": product.tagline if product else None,
            },
            "segment": {
                "code": cp.segment_code,
                "name": segment.name if segment else cp.segment_code,
            },
            "plan": {
                "code": cp.plan_code,
                "name": plan.name if plan else cp.plan_code,
                "status": cp.plan_status,
                "trial_starts_at": cp.trial_starts_at,
                "trial_ends_at": cp.trial_ends_at,
                "subscription_starts_at": cp.subscription_starts_at,
                "subscription_ends_at": cp.subscription_ends_at,
                "cancelled_at": cp.cancelled_at,
                "is_active": cp.is_active,
            },
            "is_active": cp.is_active,
            "settings": cp.settings_json or {},
            "modules": [
                {
                    "code": m.module_code,
                    "name": m.name,
                    "is_enabled": m.is_enabled,
                    "settings": m.settings_json or {},
                } for m in product_modules
            ],
        })

    return {
        "company": _company_dict(company),
        "users_count": db.query(User).filter(User.company_id == company.id).count(),
        "core_modules": get_enabled_modules_for_company(db, company.id),
        "products": product_payload,
        "controlled_by": "DSYSTEM HUB / DSYSTEM SERVER CORE",
    }


@router.get("/overview")
def admin_overview(db: Session = Depends(get_db), _=Depends(require_master_or_admin)):
    return {
        "ok": True,
        "purpose": "Rotas administrativas que serão consumidas pelo DSYSTEM HUB.",
        "totals": {
            "companies": db.query(Company).count(),
            "active_companies": db.query(Company).filter(Company.is_active == True).count(),  # noqa: E712
            "users": db.query(User).count(),
            "active_users": db.query(User).filter(User.is_active == True).count(),  # noqa: E712
            "products": db.query(Product).filter(Product.is_active == True).count(),  # noqa: E712
            "global_plans": db.query(Plan).filter(Plan.is_active == True).count(),  # noqa: E712
            "active_company_products": db.query(CompanyProduct).filter(CompanyProduct.is_active == True).count(),  # noqa: E712
            "trial_company_products": db.query(CompanyProduct).filter(CompanyProduct.plan_status == "TRIAL").count(),
            "modules": db.query(Module).filter(Module.is_active == True).count(),  # noqa: E712
            "sync_logs": db.query(SyncLog).count(),
            "audit_logs": db.query(AuditLog).count(),
        },
        "next_consumer": "DSYSTEM HUB",
    }


@router.get("/companies")
def admin_list_companies(db: Session = Depends(get_db), _=Depends(require_master_or_admin)):
    return [_company_dict(c) for c in db.query(Company).order_by(Company.name).all()]


@router.post("/companies", status_code=status.HTTP_201_CREATED)
def admin_create_company(payload: CompanyAdminCreate, db: Session = Depends(get_db), current_user=Depends(require_master_or_admin)):
    exists = db.query(Company).filter(Company.slug == payload.slug).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug da empresa já existe")
    company = Company(name=payload.name, slug=payload.slug, document=payload.document, is_active=payload.is_active)
    db.add(company)
    db.commit()
    db.refresh(company)
    write_audit(db, company_id=company.id, user_id=current_user.id, module_code="core", action="ADMIN_CREATE_COMPANY", description=f"Empresa criada: {company.slug}")
    return _company_dict(company)


@router.put("/companies/{company_id}")
def admin_update_company(company_id: int, payload: CompanyAdminUpdate, db: Session = Depends(get_db), current_user=Depends(require_master_or_admin)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada")
    if payload.slug and payload.slug != company.slug:
        exists = db.query(Company).filter(Company.slug == payload.slug).first()
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug da empresa já existe")
    for field in ["name", "slug", "document", "is_active"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(company, field, value)
    db.commit()
    db.refresh(company)
    write_audit(db, company_id=company.id, user_id=current_user.id, module_code="core", action="ADMIN_UPDATE_COMPANY", description=f"Empresa atualizada: {company.slug}")
    return _company_dict(company)


@router.get("/companies/{company_id}/config")
def admin_get_company_config(company_id: int, db: Session = Depends(get_db), _=Depends(require_master_or_admin)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada")
    return _company_config(db, company)


@router.get("/users")
def admin_list_users(company_id: int | None = None, db: Session = Depends(get_db), _=Depends(require_master_or_admin)):
    query = db.query(User)
    if company_id:
        query = query.filter(User.company_id == company_id)
    return [_user_dict(u) for u in query.order_by(User.full_name).all()]


@router.post("/users", status_code=status.HTTP_201_CREATED)
def admin_create_user(payload: UserAdminCreate, db: Session = Depends(get_db), current_user=Depends(require_master_or_admin)):
    company = db.get(Company, payload.company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada")
    exists = db.query(User).filter(User.company_id == payload.company_id, User.username == payload.username).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Usuário já existe nesta empresa")
    user = User(
        company_id=payload.company_id,
        username=payload.username,
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role.upper(),
        is_active=payload.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    write_audit(db, company_id=user.company_id, user_id=current_user.id, module_code="core", action="ADMIN_CREATE_USER", description=f"Usuário criado: {user.username}")
    return _user_dict(user)


@router.put("/users/{user_id}")
def admin_update_user(user_id: int, payload: UserAdminUpdate, db: Session = Depends(get_db), current_user=Depends(require_master_or_admin)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    if payload.username and payload.username != user.username:
        exists = db.query(User).filter(User.company_id == user.company_id, User.username == payload.username).first()
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Usuário já existe nesta empresa")
        user.username = payload.username
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.email is not None:
        user.email = payload.email
    if payload.role is not None:
        user.role = payload.role.upper()
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password:
        user.password_hash = hash_password(payload.password)
    db.commit()
    db.refresh(user)
    write_audit(db, company_id=user.company_id, user_id=current_user.id, module_code="core", action="ADMIN_UPDATE_USER", description=f"Usuário atualizado: {user.username}")
    return _user_dict(user)


@router.post("/company-modules")
def admin_upsert_company_module(payload: CompanyModuleAdminUpsert, db: Session = Depends(get_db), current_user=Depends(require_master_or_admin)):
    company = db.get(Company, payload.company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada")
    module = db.query(Module).filter(Module.code == payload.module_code).first()
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Módulo não encontrado")
    link = db.query(CompanyModule).filter(CompanyModule.company_id == payload.company_id, CompanyModule.module_id == module.id).first()
    if not link:
        link = CompanyModule(company_id=payload.company_id, module_id=module.id, plan=payload.plan, is_enabled=payload.is_enabled)
        db.add(link)
    else:
        link.plan = payload.plan
        link.is_enabled = payload.is_enabled
    db.commit()
    db.refresh(link)
    write_audit(db, company_id=payload.company_id, user_id=current_user.id, module_code="core", action="ADMIN_UPSERT_COMPANY_MODULE", description=f"Módulo {module.code}: enabled={link.is_enabled}")
    return {"ok": True, "company_id": link.company_id, "module_code": module.code, "module_name": module.name, "plan": link.plan, "is_enabled": link.is_enabled}


@router.post("/company-products")
def admin_upsert_company_product(payload: CompanyProductUpsert, db: Session = Depends(get_db), current_user=Depends(require_master_or_admin)):
    company = db.get(Company, payload.company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada")
    product = db.query(Product).filter(Product.code == payload.product_code).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")
    if payload.segment_code:
        segment = db.query(Segment).filter(Segment.product_code == payload.product_code, Segment.code == payload.segment_code).first()
        if not segment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Segmento não encontrado para esse produto")
    plan = db.query(Plan).filter(Plan.code == payload.plan_code).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plano não encontrado")

    record = db.query(CompanyProduct).filter(CompanyProduct.company_id == payload.company_id, CompanyProduct.product_code == payload.product_code).first()
    if not record:
        record = CompanyProduct(
            company_id=payload.company_id,
            product_code=payload.product_code,
            segment_code=payload.segment_code,
            plan_code=payload.plan_code,
            plan_status=payload.plan_status,
            trial_starts_at=payload.trial_starts_at,
            trial_ends_at=payload.trial_ends_at,
            subscription_starts_at=payload.subscription_starts_at,
            subscription_ends_at=payload.subscription_ends_at,
            cancelled_at=payload.cancelled_at,
            is_active=payload.is_active,
            settings_json=payload.settings_json,
        )
        db.add(record)
    else:
        record.segment_code = payload.segment_code
        record.plan_code = payload.plan_code
        record.plan_status = payload.plan_status
        record.trial_starts_at = payload.trial_starts_at
        record.trial_ends_at = payload.trial_ends_at
        record.subscription_starts_at = payload.subscription_starts_at
        record.subscription_ends_at = payload.subscription_ends_at
        record.cancelled_at = payload.cancelled_at
        record.is_active = payload.is_active
        record.settings_json = payload.settings_json
    db.commit()
    db.refresh(record)
    write_audit(db, company_id=payload.company_id, user_id=current_user.id, module_code="core", action="ADMIN_UPSERT_COMPANY_PRODUCT", description=f"Produto {payload.product_code} / segmento {payload.segment_code} / plano {payload.plan_code} / status {payload.plan_status}")
    return {"ok": True, "company_product_id": record.id, "company_id": record.company_id, "product_code": record.product_code, "segment_code": record.segment_code, "plan_code": record.plan_code, "plan_status": record.plan_status, "trial_starts_at": record.trial_starts_at, "trial_ends_at": record.trial_ends_at, "subscription_starts_at": record.subscription_starts_at, "subscription_ends_at": record.subscription_ends_at, "cancelled_at": record.cancelled_at, "is_active": record.is_active, "settings": record.settings_json or {}}


@router.patch("/company-products/{company_product_id}/plan")
def admin_update_company_product_plan(company_product_id: int, payload: CompanyProductPlanUpdate, db: Session = Depends(get_db), current_user=Depends(require_master_or_admin)):
    record = db.get(CompanyProduct, company_product_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto contratado não encontrado")
    if payload.plan_code is not None:
        plan = db.query(Plan).filter(Plan.code == payload.plan_code, Plan.is_active == True).first()  # noqa: E712
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plano global não encontrado")
        record.plan_code = payload.plan_code
    if payload.plan_status is not None:
        allowed = {"TRIAL", "ACTIVE", "SUSPENDED", "CANCELLED", "EXPIRED"}
        status_value = payload.plan_status.upper()
        if status_value not in allowed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Status inválido. Use: {sorted(allowed)}")
        record.plan_status = status_value
        if status_value == "CANCELLED":
            record.is_active = False if payload.is_active is None else payload.is_active
            record.cancelled_at = payload.cancelled_at or datetime.utcnow()
    for field in ["trial_starts_at", "trial_ends_at", "subscription_starts_at", "subscription_ends_at", "cancelled_at", "is_active"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(record, field, value)
    db.commit()
    db.refresh(record)
    write_audit(db, company_id=record.company_id, user_id=current_user.id, module_code="core", action="ADMIN_UPDATE_COMPANY_PRODUCT_PLAN", description=f"Produto {record.product_code}: plano={record.plan_code}, status={record.plan_status}")
    return {
        "ok": True,
        "company_product_id": record.id,
        "company_id": record.company_id,
        "product_code": record.product_code,
        "plan_code": record.plan_code,
        "plan_status": record.plan_status,
        "trial_starts_at": record.trial_starts_at,
        "trial_ends_at": record.trial_ends_at,
        "subscription_starts_at": record.subscription_starts_at,
        "subscription_ends_at": record.subscription_ends_at,
        "cancelled_at": record.cancelled_at,
        "is_active": record.is_active,
    }


@router.get("/plans")
def admin_list_global_plans(db: Session = Depends(get_db), _=Depends(require_master_or_admin)):
    plans = db.query(Plan).order_by(Plan.code).all()
    return [{"code": p.code, "name": p.name, "description": p.description, "scope": p.scope, "is_trial": p.is_trial, "is_active": p.is_active} for p in plans]


@router.post("/company-product-modules")
def admin_upsert_company_product_module(payload: CompanyProductModuleUpsert, db: Session = Depends(get_db), current_user=Depends(require_master_or_admin)):
    company_product = db.query(CompanyProduct).filter(CompanyProduct.company_id == payload.company_id, CompanyProduct.product_code == payload.product_code).first()
    if not company_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não contratado/ativado para esta empresa")
    record = db.query(CompanyProductModule).filter(
        CompanyProductModule.company_id == payload.company_id,
        CompanyProductModule.product_code == payload.product_code,
        CompanyProductModule.module_code == payload.module_code,
    ).first()
    name = payload.name or payload.module_code
    if not record:
        record = CompanyProductModule(
            company_id=payload.company_id,
            product_code=payload.product_code,
            module_code=payload.module_code,
            name=name,
            is_enabled=payload.is_enabled,
            settings_json=payload.settings_json,
        )
        db.add(record)
    else:
        record.name = name
        record.is_enabled = payload.is_enabled
        record.settings_json = payload.settings_json
    db.commit()
    db.refresh(record)
    write_audit(db, company_id=payload.company_id, user_id=current_user.id, module_code="core", action="ADMIN_UPSERT_COMPANY_PRODUCT_MODULE", description=f"Submódulo {payload.module_code}: enabled={payload.is_enabled}")
    return {"ok": True, "id": record.id, "company_id": record.company_id, "product_code": record.product_code, "module_code": record.module_code, "name": record.name, "is_enabled": record.is_enabled, "settings": record.settings_json or {}}


@router.get("/sync-logs")
def admin_sync_logs(company_id: int | None = None, module_code: str | None = None, limit: int = 100, db: Session = Depends(get_db), _=Depends(require_master_or_admin)):
    query = db.query(SyncLog)
    if company_id:
        query = query.filter(SyncLog.company_id == company_id)
    if module_code:
        query = query.filter(SyncLog.module_code == module_code)
    logs = query.order_by(SyncLog.id.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "company_id": l.company_id,
            "module_code": l.module_code,
            "direction": l.direction,
            "status": l.status,
            "message": l.message,
            "total_received": l.total_received,
            "total_created": l.total_created,
            "total_updated": l.total_updated,
            "total_ignored": l.total_ignored,
            "total_errors": l.total_errors,
            "created_at": l.created_at,
        } for l in logs
    ]


@router.get("/audit-logs")
def admin_audit_logs(company_id: int | None = None, module_code: str | None = None, limit: int = 100, db: Session = Depends(get_db), _=Depends(require_master_or_admin)):
    query = db.query(AuditLog)
    if company_id:
        query = query.filter(AuditLog.company_id == company_id)
    if module_code:
        query = query.filter(AuditLog.module_code == module_code)
    logs = query.order_by(AuditLog.id.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "company_id": l.company_id,
            "user_id": l.user_id,
            "module_code": l.module_code,
            "action": l.action,
            "description": l.description,
            "ip_address": l.ip_address,
            "created_at": l.created_at,
        } for l in logs
    ]
