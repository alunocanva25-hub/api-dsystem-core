from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import hash_password
from app.db.session import get_db
from app.models.company import Company
from app.models.user import User
from app.routes.deps import require_master_or_admin
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
def list_users(company_id: int | None = None, db: Session = Depends(get_db), _=Depends(require_master_or_admin)):
    query = db.query(User)
    if company_id:
        query = query.filter(User.company_id == company_id)
    return query.order_by(User.full_name).all()


@router.post("", response_model=UserResponse)
def create_user(payload: UserCreate, db: Session = Depends(get_db), _=Depends(require_master_or_admin)):
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
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
