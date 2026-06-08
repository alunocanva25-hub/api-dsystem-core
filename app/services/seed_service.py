from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.security import hash_password
from app.models.company import Company
from app.models.user import User
from app.models.module import Module, CompanyModule
from app.models.product_config import Product, Segment, Plan, CompanyProduct, CompanyProductModule

DEFAULT_MODULES = [
    ("core", "DSYSTEM SERVER CORE", "API central do ecossistema DSYSTEM."),
    ("hub", "DSYSTEM HUB", "Painel geral para controle do ecossistema DSYSTEM."),
    ("studio", "DSYSTEM STUDIO", "Sistema principal desktop do DSYSTEM STUDIO."),
    ("studio_go", "DS STUDIO GO", "Cliente mobile/PWA do DSYSTEM STUDIO."),
    ("dsystem_ar", "DSYSTEM AR", "Scanner/rotina mobile de AR já em operação."),
    ("dsystem_ar_painel", "DSYSTEM-AR-PAINEL", "Painel local do DSYSTEM AR, futuramente conectado à API CORE."),
    ("pulselab", "PulseLab", "Sistema de aferição de medidores."),
    ("vision", "DSYSTEM VISION", "Gestão inteligente para óticas."),
    ("bike", "DSYSTEM BIKE", "Gestão de oficinas de bicicleta."),
    ("retail", "DSYSTEM RETAIL", "DSYSTEM RETAIL — Gestão inteligente para o varejo."),
    ("vm", "Gestor V&M", "Gestão para vidros e mármore."),
    ("inventario", "Inventário", "Relatórios e rotinas de inventário."),
    ("winthor_tools", "WinThor Tools", "Ferramentas e automações WinThor/Oracle."),
]

DEFAULT_PRODUCTS = [
    ("retail", "DSYSTEM RETAIL", "DSYSTEM RETAIL — Gestão inteligente para o varejo.", "Sistema único para varejo com comportamento configurável por segmento."),
    ("studio", "DSYSTEM STUDIO", "Gestão inteligente para estúdios e salões.", "Desktop principal do DSYSTEM STUDIO."),
    ("studio_go", "DS STUDIO GO", "Cliente mobile/PWA do DSYSTEM STUDIO.", "Aplicativo mobile/PWA consumidor da API."),
    ("dsystem_ar", "DSYSTEM AR", "Scanner AR do ecossistema DSYSTEM.", "Aplicativo/rotina de AR já em operação."),
    ("dsystem_ar_painel", "DSYSTEM-AR-PAINEL", "Painel operacional do DSYSTEM AR.", "Painel local atual que futuramente consumirá a API CORE."),
    ("pulselab", "PulseLab", "Sistema de aferição de medidores.", "Projeto PulseLab dentro do ecossistema DSYSTEM."),
    ("vision", "DSYSTEM VISION", "Gestão inteligente para óticas.", "Produto para óticas baseado no padrão DSYSTEM."),
]

RETAIL_SEGMENTS = [
    ("retail", "MARKET", "Mercadinho / Supermercado", "Segmento para mercadinhos, supermercados e mercados."),
    ("retail", "CONVENIENCE", "Conveniência", "Segmento para lojas de conveniência."),
    ("retail", "CONSTRUCTION", "Material de construção", "Segmento para lojas de material de construção."),
    ("retail", "GENERAL_STORE", "Loja geral", "Segmento genérico para varejo geral."),
]

DEFAULT_PLANS = [
    ("TRIAL", "Teste", "Plano de teste/avaliação controlado pelo DSYSTEM HUB.", True),
    ("STARTER", "Inicial", "Plano inicial para qualquer produto DSYSTEM.", False),
    ("BASIC", "Básico", "Plano básico para qualquer produto DSYSTEM.", False),
    ("PRO", "Profissional", "Plano profissional para operação completa.", False),
    ("BUSINESS", "Empresarial", "Plano empresarial para operação avançada.", False),
    ("ENTERPRISE", "Enterprise", "Plano corporativo sob medida.", False),
]

LEGACY_PLAN_ALIASES = {
    "BASICO": "BASIC",
    "PROFISSIONAL": "PRO",
    "PREMIUM": "BUSINESS",
}

PLAN_STATUSES = ["TRIAL", "ACTIVE", "SUSPENDED", "CANCELLED", "EXPIRED"]

RETAIL_DEFAULT_MODULES = [
    ("retail.dashboard", "Dashboard"),
    ("retail.products", "Produtos"),
    ("retail.stock", "Estoque"),
    ("retail.pdv", "PDV"),
    ("retail.purchases", "Compras"),
    ("retail.suppliers", "Fornecedores"),
    ("retail.financial", "Financeiro"),
    ("retail.reports", "Relatórios"),
    ("retail.losses", "Perdas"),
    ("retail.expiration", "Validade"),
]

RETAIL_DEFAULT_SETTINGS = {
    "controlled_by": "DSYSTEM HUB / DSYSTEM SERVER CORE",
    "client_can_choose_segment": False,
    "uses_expiration_control": True,
    "uses_loss_control": True,
    "uses_stock_control": True,
    "uses_pdv": True,
    "uses_suppliers": True,
    "segment_behavior": "MARKET",
}


def seed_database(db: Session):
    settings = get_settings()

    company = db.query(Company).filter(Company.slug == settings.default_company_slug).first()
    if not company:
        company = Company(name=settings.default_company_name, slug=settings.default_company_slug, document=None)
        db.add(company)
        db.commit()
        db.refresh(company)

    # Desativa módulo legado se existir em bancos antigos; ele saiu do padrão oficial.
    legacy = db.query(Module).filter(Module.code == "pousada").first()
    if legacy:
        legacy.is_active = False
        db.commit()

    for code, name, description in DEFAULT_MODULES:
        module = db.query(Module).filter(Module.code == code).first()
        if not module:
            module = Module(code=code, name=name, description=description)
            db.add(module)
            db.commit()
            db.refresh(module)
        else:
            module.name = name
            module.description = description
            module.is_active = True
            db.commit()
        exists = db.query(CompanyModule).filter(
            CompanyModule.company_id == company.id,
            CompanyModule.module_id == module.id,
        ).first()
        if not exists:
            db.add(CompanyModule(company_id=company.id, module_id=module.id, plan="core", is_enabled=True))
            db.commit()

    for code, name, tagline, description in DEFAULT_PRODUCTS:
        product = db.query(Product).filter(Product.code == code).first()
        if not product:
            db.add(Product(code=code, name=name, tagline=tagline, description=description, is_active=True))
        else:
            product.name = name
            product.tagline = tagline
            product.description = description
            product.is_active = True
        db.commit()

    for product_code, code, name, description in RETAIL_SEGMENTS:
        segment = db.query(Segment).filter(Segment.product_code == product_code, Segment.code == code).first()
        if not segment:
            db.add(Segment(product_code=product_code, code=code, name=name, description=description, is_active=True))
        else:
            segment.name = name
            segment.description = description
            segment.is_active = True
        db.commit()

    # Desativa códigos antigos mantendo compatibilidade histórica.
    for legacy_code in LEGACY_PLAN_ALIASES:
        legacy_plan = db.query(Plan).filter(Plan.code == legacy_code).first()
        if legacy_plan:
            legacy_plan.is_active = False
            db.commit()

    for code, name, description, is_trial in DEFAULT_PLANS:
        plan = db.query(Plan).filter(Plan.code == code).first()
        if not plan:
            db.add(Plan(code=code, name=name, description=description, scope="GLOBAL", is_trial=is_trial, is_active=True))
        else:
            plan.name = name
            plan.description = description
            plan.scope = "GLOBAL"
            plan.is_trial = is_trial
            plan.is_active = True
        db.commit()

    company_product = db.query(CompanyProduct).filter(
        CompanyProduct.company_id == company.id,
        CompanyProduct.product_code == "retail",
    ).first()
    if not company_product:
        db.add(CompanyProduct(
            company_id=company.id,
            product_code="retail",
            segment_code="MARKET",
            plan_code="TRIAL",
            plan_status="TRIAL",
            is_active=True,
            settings_json=RETAIL_DEFAULT_SETTINGS,
        ))
        db.commit()
    else:
        company_product.segment_code = company_product.segment_code or "MARKET"
        company_product.plan_code = LEGACY_PLAN_ALIASES.get(company_product.plan_code, company_product.plan_code or "TRIAL")
        company_product.plan_status = getattr(company_product, "plan_status", None) or ("TRIAL" if company_product.plan_code == "TRIAL" else "ACTIVE")
        company_product.settings_json = company_product.settings_json or RETAIL_DEFAULT_SETTINGS
        company_product.is_active = True
        db.commit()

    for module_code, name in RETAIL_DEFAULT_MODULES:
        cpm = db.query(CompanyProductModule).filter(
            CompanyProductModule.company_id == company.id,
            CompanyProductModule.product_code == "retail",
            CompanyProductModule.module_code == module_code,
        ).first()
        if not cpm:
            db.add(CompanyProductModule(
                company_id=company.id,
                product_code="retail",
                module_code=module_code,
                name=name,
                is_enabled=True,
                settings_json={},
            ))
        else:
            cpm.name = name
            cpm.is_enabled = True
        db.commit()

    user = db.query(User).filter(User.company_id == company.id, User.username == settings.master_username).first()
    if not user:
        user = User(
            company_id=company.id,
            username=settings.master_username,
            full_name=settings.master_full_name,
            email=settings.master_email,
            password_hash=hash_password(settings.master_password),
            role="MASTER",
            is_active=True,
        )
        db.add(user)
        db.commit()
