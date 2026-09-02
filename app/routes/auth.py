from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.security import create_access_token, verify_password_flexible
from app.db.session import get_db
from app.models.company import Company
from app.models.user import User
from app.routes.deps import get_current_user
from app.schemas.auth import LoginRequest, MeResponse, TokenResponse, TokenValidationResponse
from app.services.audit_service import write_audit
from app.services.module_service import build_user_session

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _find_user_for_login(db: Session, payload: LoginRequest) -> User | None:
    query = db.query(User).filter(User.username == payload.username)
    if payload.company_slug:
        company = db.query(Company).filter(Company.slug == payload.company_slug).first()
        if not company:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Empresa não encontrada")
        query = query.filter(User.company_id == company.id)
    return query.first()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    settings = get_settings()
    user = _find_user_for_login(db, payload)
    if not user or not verify_password_flexible(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário ou senha inválidos")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuário inativo")

    token = create_access_token({"sub": str(user.id), "company_id": user.company_id, "role": user.role})
    write_audit(
        db,
        company_id=user.company_id,
        user_id=user.id,
        module_code="core",
        action="LOGIN",
        description="Login realizado com sucesso",
        ip_address=request.client.host if request.client else None,
    )
    session = build_user_session(db, user)
    return {
        "ok": True,
        "success": True,
        "access_token": token,
        "token": token,
        "token_type": "bearer",
        "expires_in_minutes": settings.access_token_expire_minutes,
        "user": session,
        "company": session.get("company"),
        "modules": session.get("modules", []),
    }


@router.get("/me", response_model=MeResponse)
def me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return build_user_session(db, current_user)


@router.get("/session", response_model=MeResponse)
def session(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Atalho para aplicativos recuperarem contexto completo após abrir."""
    return build_user_session(db, current_user)


@router.get("/validate", response_model=TokenValidationResponse)
def validate_token(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {"ok": True, "user": build_user_session(db, current_user)}

@router.get("/permissions")
def permissions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retorna somente as permissões calculadas do usuário logado."""
    return build_user_session(db, current_user)["permissions"]


@router.get("/context")
def context(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Contexto completo para HUB, GO, STUDIO e módulos futuros."""
    return {
        "ok": True,
        "session": build_user_session(db, current_user),
        "security_note": "Permissões calculadas por perfil e módulos liberados para a empresa.",
    }
