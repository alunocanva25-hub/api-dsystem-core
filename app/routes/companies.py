from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.company import Company
from app.routes.deps import require_master_or_admin
from app.schemas.company import CompanyCreate, CompanyResponse

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("", response_model=list[CompanyResponse])
def list_companies(db: Session = Depends(get_db), _=Depends(require_master_or_admin)):
    return db.query(Company).order_by(Company.name).all()


@router.post("", response_model=CompanyResponse)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db), _=Depends(require_master_or_admin)):
    exists = db.query(Company).filter(Company.slug == payload.slug).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug da empresa já existe")
    company = Company(name=payload.name, slug=payload.slug, document=payload.document)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company
