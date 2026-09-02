from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.module import CompanyModule, Module
from app.routes.deps import get_current_user, require_master_or_admin
from app.schemas.module import DisableCompanyModuleRequest, EnableCompanyModuleRequest, ModuleResponse
from app.services.module_service import get_enabled_modules_for_company

router = APIRouter(prefix="/api", tags=["modules"])


def _module_link_dict(link: CompanyModule, module: Module | None = None):
    module = module or getattr(link, "module", None)
    return {
        "id": link.id,
        "company_id": link.company_id,
        "module_id": link.module_id,
        "module_code": module.code if module else None,
        "module_name": module.name if module else None,
        "plan": link.plan,
        "is_enabled": link.is_enabled,
    }


@router.get("/modules", response_model=list[ModuleResponse])
def list_modules(db: Session = Depends(get_db), _=Depends(require_master_or_admin)):
    return db.query(Module).order_by(Module.name).all()


@router.get("/my/modules")
def list_my_modules(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return get_enabled_modules_for_company(db, current_user.company_id)


@router.get("/companies/{company_id}/modules")
def list_company_modules(company_id: int, db: Session = Depends(get_db), _=Depends(require_master_or_admin)):
    rows = (
        db.query(CompanyModule, Module)
        .join(Module, Module.id == CompanyModule.module_id)
        .filter(CompanyModule.company_id == company_id)
        .order_by(Module.name)
        .all()
    )
    return [_module_link_dict(link, module) for link, module in rows]


@router.post("/company-modules/enable")
def enable_company_module(payload: EnableCompanyModuleRequest, db: Session = Depends(get_db), _=Depends(require_master_or_admin)):
    module = db.query(Module).filter(Module.code == payload.module_code).first()
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Módulo não encontrado")
    link = db.query(CompanyModule).filter(
        CompanyModule.company_id == payload.company_id,
        CompanyModule.module_id == module.id,
    ).first()
    if link:
        link.is_enabled = True
        link.plan = payload.plan
    else:
        link = CompanyModule(company_id=payload.company_id, module_id=module.id, plan=payload.plan, is_enabled=True)
        db.add(link)
    db.commit()
    db.refresh(link)
    return {"ok": True, **_module_link_dict(link, module)}


@router.post("/company-modules/disable")
def disable_company_module(payload: DisableCompanyModuleRequest, db: Session = Depends(get_db), _=Depends(require_master_or_admin)):
    module = db.query(Module).filter(Module.code == payload.module_code).first()
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Módulo não encontrado")
    link = db.query(CompanyModule).filter(
        CompanyModule.company_id == payload.company_id,
        CompanyModule.module_id == module.id,
    ).first()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Módulo não vinculado à empresa")
    link.is_enabled = False
    db.commit()
    db.refresh(link)
    return {"ok": True, **_module_link_dict(link, module)}
