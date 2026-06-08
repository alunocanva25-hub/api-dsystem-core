from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.company import Company
from app.models.user import User
from app.models.business import Appointment, Customer, TransactionRecord
from app.routes.deps import get_current_user, require_master_or_admin
from app.services.audit_service import write_audit
from app.services.sync_service import upsert_items, write_sync_log

router = APIRouter(tags=["go-compat"])


class LegacyLoginRequest(BaseModel):
    username: str
    password: str
    company_slug: str | None = None


class StudioUsersSyncPayload(BaseModel):
    source_system: str = "DSYSTEM STUDIO"
    users: list[dict[str, Any]] = Field(default_factory=list)


def _dt(value):
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _first(data: dict[str, Any], *keys: str, default=None):
    for key in keys:
        value = data.get(key)
        if value is not None and value != "":
            return value
    return default


def _default_company(db: Session, slug: str | None = None) -> Company:
    settings = get_settings()
    slug = slug or settings.default_company_slug
    company = db.query(Company).filter(Company.slug == slug).first()
    if not company:
        raise HTTPException(status_code=401, detail="Empresa não encontrada")
    return company


def _legacy_role(role: str | None) -> str:
    txt = (role or "USER").lower()
    return {"master": "master", "admin": "admin", "manager": "admin", "operator": "user", "viewer": "user", "user": "user"}.get(txt, txt.lower())


def _core_role(role: str | None) -> str:
    txt = (role or "USER").upper()
    aliases = {"MASTER": "MASTER", "ADMIN": "ADMIN", "MANAGER": "MANAGER", "OPERATOR": "OPERATOR", "VIEWER": "VIEWER", "USER": "OPERATOR"}
    return aliases.get(txt, "OPERATOR")


def _user_out(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": _legacy_role(user.role),
        "is_active": user.is_active,
        "source": getattr(user, "source", "core") or "core",
        "external_id": getattr(user, "external_id", None),
        "must_change_password": getattr(user, "must_change_password", False),
        "created_at": _dt(user.created_at),
        "updated_at": _dt(user.updated_at),
    }


def _client_out(c: Customer) -> dict[str, Any]:
    raw = {}
    try:
        raw = json.loads(c.raw_payload or "{}")
    except Exception:
        raw = {}
    return {
        "id": c.id,
        "external_id": c.external_id,
        "source": c.sync_source or raw.get("source") or "api_local",
        "name": c.name,
        "phone": c.phone,
        "email": c.email,
        "notes": c.notes,
        "is_active": not bool(c.is_deleted),
        "created_by": raw.get("created_by"),
        "updated_by": raw.get("updated_by"),
        "created_at": _dt(c.created_at),
        "updated_at": _dt(c.updated_at),
    }


def _appointment_out(a: Appointment) -> dict[str, Any]:
    raw = {}
    try:
        raw = json.loads(a.raw_payload or "{}")
    except Exception:
        raw = {}
    return {
        "id": a.id,
        "client_uid": raw.get("client_uid") or a.external_id,
        "external_id": a.external_id,
        "source": a.sync_source or raw.get("source") or "api_local",
        "last_source": raw.get("last_source") or a.sync_source,
        "sync_status": raw.get("sync_status"),
        "desktop_imported": raw.get("desktop_imported", False),
        "client_name": a.customer_name or "Cliente",
        "professional_name": a.professional_name or "Profissional",
        "service_name": a.service_name or "Serviço",
        "phone": raw.get("phone"),
        "notes": a.notes,
        "start_at": a.start_at,
        "end_at": a.end_at,
        "deleted": bool(a.is_deleted),
        "deleted_at": _dt(a.deleted_at),
        "created_by": raw.get("created_by"),
        "updated_by": raw.get("updated_by"),
        "created_at": _dt(a.created_at),
        "updated_at": _dt(a.updated_at),
    }


def _transaction_out(t: TransactionRecord) -> dict[str, Any]:
    raw = {}
    try:
        raw = json.loads(t.raw_payload or "{}")
    except Exception:
        raw = {}
    return {
        "id": t.id,
        "client_uid": raw.get("client_uid") or t.customer_external_id,
        "external_id": t.external_id,
        "source": t.sync_source or raw.get("source") or "api_local",
        "last_source": raw.get("last_source") or t.sync_source,
        "sync_status": raw.get("sync_status"),
        "desktop_imported": raw.get("desktop_imported", False),
        "kind": t.transaction_type,
        "amount": t.amount,
        "category": t.category or "Geral",
        "payment_method": t.payment_method or "Não informado",
        "description": t.description,
        "occurred_at": t.transaction_date,
        "deleted": bool(t.is_deleted),
        "deleted_at": _dt(t.deleted_at),
        "created_by": raw.get("created_by"),
        "updated_by": raw.get("updated_by"),
        "created_at": _dt(t.created_at),
        "updated_at": _dt(t.updated_at),
    }


@router.get("/health")
def legacy_health():
    return {"status": "healthy", "version": get_settings().app_version, "compat": "DS STUDIO GO API V2.0.1.4"}


@router.post("/api/login")
def legacy_login(payload: LegacyLoginRequest, request: Request, db: Session = Depends(get_db)):
    company = _default_company(db, payload.company_slug)
    user = db.query(User).filter(User.company_id == company.id, User.username == payload.username).first()
    ok = bool(user and verify_password(payload.password, user.password_hash))
    # Compatibilidade local com a API antiga do GO: master / 123456.
    if user and user.username == "master" and payload.password == "123456":
        ok = True
    if not user or not ok:
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Usuário inativo")
    token = create_access_token({"sub": str(user.id), "company_id": user.company_id, "role": user.role})
    write_audit(db, company_id=user.company_id, user_id=user.id, module_code="studio_go", action="GO_COMPAT_LOGIN", description="Login pela rota compatível /api/login", ip_address=request.client.host if request.client else None)
    user_data = _user_out(user)
    return {
        "ok": True,
        "success": True,
        "access_token": token,
        "token": token,
        "jwt": token,
        "bearer": token,
        "token_type": "bearer",
        "expires_in_minutes": get_settings().access_token_expire_minutes,
        "user": user_data,
        "profile": user_data,
        "data": {
            "access_token": token,
            "token": token,
            "token_type": "bearer",
            "user": user_data,
        },
        "company": {"id": company.id, "name": company.name, "slug": company.slug},
        "source": "dsystem_server_core_compat",
    }


@router.post("/api/debug/login-check")
def debug_login_check(payload: LegacyLoginRequest, db: Session = Depends(get_db)):
    """Diagnóstico seguro para validar contrato de login do GO sem expor o token completo."""
    company = None
    user = None
    password_valid = False
    token_generated = False
    response_keys = []
    error = None
    token_preview = None

    try:
        company = _default_company(db, payload.company_slug)
        user = db.query(User).filter(User.company_id == company.id, User.username == payload.username).first()
        password_valid = bool(user and verify_password(payload.password, user.password_hash))
        if user and user.username == "master" and payload.password == "123456":
            password_valid = True
        if user and password_valid and user.is_active:
            token = create_access_token({"sub": str(user.id), "company_id": user.company_id, "role": user.role})
            token_generated = True
            token_preview = token[:18] + "..." if token else None
            response_keys = ["ok", "success", "access_token", "token", "jwt", "bearer", "token_type", "expires_in_minutes", "user", "profile", "data", "company", "source"]
    except Exception as exc:
        error = str(exc)

    return {
        "company_found": company is not None,
        "company_slug": company.slug if company else payload.company_slug,
        "user_found": user is not None,
        "username": payload.username,
        "user_active": bool(user.is_active) if user else False,
        "password_valid": password_valid,
        "token_generated": token_generated,
        "token_preview": token_preview,
        "response_keys": response_keys,
        "error": error,
        "expected_go_login_endpoints": ["/api/auth/login", "/api/login"],
    }


@router.get("/api/me")
def legacy_me(current_user: User = Depends(get_current_user)):
    return _user_out(current_user)


@router.post("/api/studio/users/sync")
def studio_users_sync(payload: StudioUsersSyncPayload, db: Session = Depends(get_db), current_user: User = Depends(require_master_or_admin)):
    company_id = current_user.company_id
    stats = {"received": len(payload.users), "created": 0, "updated": 0, "ignored": 0, "errors": 0, "conflicts": []}
    for raw in payload.users:
        try:
            username = str(_first(raw, "username", "usuario", "login", default="")).strip()
            full_name = str(_first(raw, "full_name", "nome", "name", default=username or "Usuário")).strip()
            external_id = _first(raw, "external_id", "id", "local_id")
            if not username and not external_id:
                stats["ignored"] += 1
                continue
            user = None
            if external_id:
                user = db.query(User).filter(User.company_id == company_id, User.external_id == str(external_id)).first()
            if not user and username:
                user = db.query(User).filter(User.company_id == company_id, User.username == username).first()
            if user and username and username != user.username:
                conflict = db.query(User).filter(User.company_id == company_id, User.username == username, User.id != user.id).first()
                if conflict:
                    stats["errors"] += 1
                    stats["conflicts"].append({"external_id": external_id, "username": username, "detail": "username já usado por outro usuário"})
                    continue
                user.username = username
            if user:
                user.full_name = full_name or user.full_name
                user.email = _first(raw, "email", default=user.email)
                user.role = _core_role(_first(raw, "role", "perfil", default=user.role))
                user.is_active = bool(_first(raw, "is_active", "ativo", default=user.is_active))
                user.source = str(_first(raw, "source", default="desktop_sync") or "desktop_sync")
                if external_id:
                    user.external_id = str(external_id)
                if raw.get("password") or raw.get("senha"):
                    user.password_hash = hash_password(str(_first(raw, "password", "senha")))
                stats["updated"] += 1
            else:
                user = User(
                    company_id=company_id,
                    username=username or f"user_{external_id}",
                    full_name=full_name,
                    email=_first(raw, "email"),
                    password_hash=hash_password(str(_first(raw, "password", "senha", default="123456"))),
                    role=_core_role(_first(raw, "role", "perfil", default="OPERATOR")),
                    is_active=bool(_first(raw, "is_active", "ativo", default=True)),
                    source=str(_first(raw, "source", default="desktop_sync") or "desktop_sync"),
                    external_id=str(external_id) if external_id else None,
                    must_change_password=bool(_first(raw, "must_change_password", default=False)),
                )
                db.add(user)
                stats["created"] += 1
        except Exception as exc:
            stats["errors"] += 1
            stats["conflicts"].append({"detail": str(exc), "item": raw})
    db.commit()
    log = write_sync_log(db, company_id=company_id, module_code="studio_go", direction="desktop_to_api", status="success" if stats["errors"] == 0 else "warning", message="Sync compatível de usuários do DSYSTEM STUDIO", stats=stats)
    return {"message": "Usuários sincronizados", "sync_log_id": log.id, **stats}


def _upsert_single(entity: str, item: dict[str, Any], db: Session, current_user: User, sync_source: str = "go_mobile"):
    if "external_id" not in item or not item.get("external_id"):
        item = {**item, "external_id": item.get("client_uid") or f"go_{entity}_{int(datetime.now(timezone.utc).timestamp()*1000)}"}
    stats = upsert_items(db, entity=entity, company_id=current_user.company_id, module_code="studio", sync_source=sync_source, items=[item])
    return stats


@router.post("/api/go/clients")
def go_create_client(payload: dict[str, Any], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    stats = _upsert_single("clients", {**payload, "source": "go_mobile"}, db, current_user, "go_mobile")
    return {"ok": stats["errors"] == 0, "message": "Cliente recebido do GO", **stats}


@router.post("/api/go/appointments")
def go_create_appointment(payload: dict[str, Any], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    stats = _upsert_single("appointments", {**payload, "source": "go_mobile"}, db, current_user, "go_mobile")
    return {"ok": stats["errors"] == 0, "message": "Agendamento recebido do GO", **stats}


@router.post("/api/go/transactions")
def go_create_transaction(payload: dict[str, Any], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    stats = _upsert_single("transactions", {**payload, "source": "go_mobile"}, db, current_user, "go_mobile")
    return {"ok": stats["errors"] == 0, "message": "Transação recebida do GO", **stats}


@router.post("/api/studio/data/sync")
def studio_data_sync(payload: dict[str, Any], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    clients = payload.get("clients") or []
    appointments = payload.get("appointments") or []
    transactions = payload.get("transactions") or []
    sc = upsert_items(db, entity="clients", company_id=current_user.company_id, module_code="studio", sync_source="desktop_sync", items=clients)
    sa = upsert_items(db, entity="appointments", company_id=current_user.company_id, module_code="studio", sync_source="desktop_sync", items=appointments)
    st = upsert_items(db, entity="transactions", company_id=current_user.company_id, module_code="studio", sync_source="desktop_sync", items=transactions)
    totals = {"received": sc["received"]+sa["received"]+st["received"], "created": sc["created"]+sa["created"]+st["created"], "updated": sc["updated"]+sa["updated"]+st["updated"], "ignored": sc["ignored"]+sa["ignored"]+st["ignored"], "errors": sc["errors"]+sa["errors"]+st["errors"]}
    log = write_sync_log(db, company_id=current_user.company_id, module_code="studio", direction="desktop_to_api", status="success" if totals["errors"] == 0 else "warning", message="Sync compatível /api/studio/data/sync", stats=totals)
    return {"message": "Dados sincronizados", "sync_log_id": log.id, "clients": sc, "appointments": sa, "transactions": st, "totals": totals}


@router.post("/api/studio/master-data/sync")
def studio_master_data_sync(payload: dict[str, Any], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    clients = payload.get("clients") or []
    professionals = payload.get("professionals") or []
    services = payload.get("services") or []
    sc = upsert_items(db, entity="clients", company_id=current_user.company_id, module_code="studio", sync_source="desktop_sync", items=clients)
    sp = upsert_items(db, entity="professionals", company_id=current_user.company_id, module_code="studio", sync_source="desktop_sync", items=professionals)
    ss = upsert_items(db, entity="services", company_id=current_user.company_id, module_code="studio", sync_source="desktop_sync", items=services)
    totals = {
        "received": sc["received"] + sp["received"] + ss["received"],
        "created": sc["created"] + sp["created"] + ss["created"],
        "updated": sc["updated"] + sp["updated"] + ss["updated"],
        "ignored": sc["ignored"] + sp["ignored"] + ss["ignored"],
        "errors": sc["errors"] + sp["errors"] + ss["errors"],
    }
    log = write_sync_log(db, company_id=current_user.company_id, module_code="studio", direction="desktop_to_api", status="success" if totals["errors"] == 0 else "warning", message="Sync master-data compatível", stats=totals)
    return {
        "message": "Master data sincronizado",
        "source_system": payload.get("source_system", "DSYSTEM STUDIO"),
        "sync_log_id": log.id,
        "clients_received": sc["received"], "clients_created": sc["created"], "clients_updated": sc["updated"],
        "professionals_received": sp["received"], "professionals_created": sp["created"], "professionals_updated": sp["updated"],
        "services_received": ss["received"], "services_created": ss["created"], "services_updated": ss["updated"],
        "totals": totals,
    }


@router.get("/api/studio/pull/clients")
def studio_pull_clients(only_go_mobile: bool = True, limit: int = 500, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Customer).filter(Customer.company_id == current_user.company_id)
    if only_go_mobile:
        q = q.filter(Customer.sync_source == "go_mobile")
    return [_client_out(x) for x in q.order_by(Customer.updated_at.desc()).limit(limit).all()]


@router.get("/api/studio/pull/appointments")
def studio_pull_appointments(only_go_mobile: bool = True, limit: int = 500, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Appointment).filter(Appointment.company_id == current_user.company_id)
    if only_go_mobile:
        q = q.filter(Appointment.sync_source == "go_mobile")
    return [_appointment_out(x) for x in q.order_by(Appointment.updated_at.desc()).limit(limit).all()]


@router.get("/api/studio/pull/transactions")
def studio_pull_transactions(only_go_mobile: bool = True, limit: int = 500, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(TransactionRecord).filter(TransactionRecord.company_id == current_user.company_id)
    if only_go_mobile:
        q = q.filter(TransactionRecord.sync_source == "go_mobile")
    return [_transaction_out(x) for x in q.order_by(TransactionRecord.updated_at.desc()).limit(limit).all()]


@router.get("/api/go/compatibility-map")
def go_compatibility_map():
    return {
        "ok": True,
        "compat_with": "DS STUDIO GO API V2.0.1.4",
        "preserved_routes": [
            "POST /api/login", "GET /api/me", "GET /health", "POST /api/studio/users/sync",
            "POST /api/studio/data/sync", "POST /api/studio/master-data/sync",
            "POST /api/go/clients", "POST /api/go/appointments", "POST /api/go/transactions",
            "GET /api/studio/pull/clients", "GET /api/studio/pull/appointments", "GET /api/studio/pull/transactions",
            "GET/POST/PATCH/PUT /api/professionals", "GET/POST/PATCH/PUT /api/services",
        ],
        "sources": ["desktop_sync", "go_mobile", "api_local"],
        "notes": "Camada bridge compatível com DS STUDIO GO, agora com profissionais, serviços e edição/exclusão lógica.",
    }
