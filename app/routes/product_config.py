from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.company import Company
from app.models.product_config import Product, Segment, Plan, CompanyProduct, CompanyProductModule

router = APIRouter(prefix="/api/core", tags=["products-segments-plans"])


@router.get("/products")
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.is_active == True).order_by(Product.code).all()  # noqa: E712
    return [{"code": p.code, "name": p.name, "tagline": p.tagline, "description": p.description} for p in products]


@router.get("/segments")
def list_segments(product_code: str | None = Query(default=None), db: Session = Depends(get_db)):
    query = db.query(Segment).filter(Segment.is_active == True)  # noqa: E712
    if product_code:
        query = query.filter(Segment.product_code == product_code)
    segments = query.order_by(Segment.product_code, Segment.code).all()
    return [{"product_code": s.product_code, "code": s.code, "name": s.name, "description": s.description} for s in segments]


@router.get("/plans")
def list_plans(db: Session = Depends(get_db)):
    plans = db.query(Plan).filter(Plan.is_active == True).order_by(Plan.code).all()  # noqa: E712
    return [{"code": p.code, "name": p.name, "description": p.description, "scope": p.scope, "is_trial": p.is_trial} for p in plans]


@router.get("/retail-standards")
def retail_standards():
    return {
        "product": {
            "code": "retail",
            "name": "DSYSTEM RETAIL",
            "commercial_name": "DSYSTEM RETAIL — Gestão inteligente para o varejo.",
            "architecture_rule": "O cliente final não escolhe o nicho no sistema. O DSYSTEM HUB / SERVER CORE configura o segmento no cadastro da empresa.",
        },
        "segments": [
            {"code": "MARKET", "name": "Mercadinho / Supermercado"},
            {"code": "CONVENIENCE", "name": "Conveniência"},
            {"code": "CONSTRUCTION", "name": "Material de construção"},
            {"code": "GENERAL_STORE", "name": "Loja geral"},
        ],
        "plans": ["TRIAL", "STARTER", "BASIC", "PRO", "BUSINESS", "ENTERPRISE"],
        "plan_rule": "Planos são globais para todos os produtos DSYSTEM; o HUB pode ativar, suspender, cancelar ou trocar o plano de qualquer produto.",
        "plan_statuses": ["TRIAL", "ACTIVE", "SUSPENDED", "CANCELLED", "EXPIRED"],
        "default_market_modules": [
            "retail.dashboard", "retail.products", "retail.stock", "retail.pdv", "retail.purchases",
            "retail.suppliers", "retail.financial", "retail.reports", "retail.losses", "retail.expiration",
        ],
        "login_behavior": "O RETAIL deve receber product_code, segment_code, plan_code, módulos liberados e settings_json da API no login/sync.",
    }


@router.get("/company-product-config")
def company_product_config(
    company_slug: str = Query(default="dsystem-master"),
    product_code: str = Query(default="retail"),
    db: Session = Depends(get_db),
):
    company = db.query(Company).filter(Company.slug == company_slug).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    company_product = db.query(CompanyProduct).filter(
        CompanyProduct.company_id == company.id,
        CompanyProduct.product_code == product_code,
        CompanyProduct.is_active == True,  # noqa: E712
    ).first()
    if not company_product:
        raise HTTPException(status_code=404, detail="Produto não configurado para esta empresa")

    modules = db.query(CompanyProductModule).filter(
        CompanyProductModule.company_id == company.id,
        CompanyProductModule.product_code == product_code,
    ).order_by(CompanyProductModule.module_code).all()

    segment = None
    if company_product.segment_code:
        segment = db.query(Segment).filter(
            Segment.product_code == product_code,
            Segment.code == company_product.segment_code,
        ).first()

    plan = db.query(Plan).filter(Plan.code == company_product.plan_code).first()

    return {
        "company": {"id": company.id, "name": company.name, "slug": company.slug},
        "product": {"code": product_code, "name": "DSYSTEM RETAIL" if product_code == "retail" else product_code},
        "segment": {
            "code": company_product.segment_code,
            "name": segment.name if segment else company_product.segment_code,
        },
        "plan": {
            "code": company_product.plan_code,
            "name": plan.name if plan else company_product.plan_code,
            "status": company_product.plan_status,
            "trial_starts_at": company_product.trial_starts_at,
            "trial_ends_at": company_product.trial_ends_at,
            "subscription_starts_at": company_product.subscription_starts_at,
            "subscription_ends_at": company_product.subscription_ends_at,
            "cancelled_at": company_product.cancelled_at,
            "is_active": company_product.is_active,
        },
        "enabled_modules": [
            {"code": m.module_code, "name": m.name, "settings": m.settings_json or {}}
            for m in modules if m.is_enabled
        ],
        "disabled_modules": [
            {"code": m.module_code, "name": m.name}
            for m in modules if not m.is_enabled
        ],
        "settings": company_product.settings_json or {},
        "controlled_by": "DSYSTEM HUB / DSYSTEM SERVER CORE",
    }
