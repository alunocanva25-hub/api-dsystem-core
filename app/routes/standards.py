from fastapi import APIRouter
from app.core.config import get_settings
from app.services.permission_service import ROLE_STANDARDS

router = APIRouter(prefix="/api/core", tags=["core-standards"])


OFFICIAL_MODULES = [
    {"code": "core", "name": "DSYSTEM SERVER CORE", "role": "API central/base do ecossistema"},
    {"code": "hub", "name": "DSYSTEM HUB", "role": "Painel geral de controle"},
    {"code": "studio", "name": "DSYSTEM STUDIO", "role": "Desktop principal"},
    {"code": "studio_go", "name": "DS STUDIO GO", "role": "Mobile/PWA consumidor da API"},
    {"code": "dsystem_ar", "name": "DSYSTEM AR", "role": "Scanner/rotina AR já existente"},
    {"code": "dsystem_ar_painel", "name": "DSYSTEM-AR-PAINEL", "role": "Painel local do AR, futuro consumidor da API CORE"},
    {"code": "pulselab", "name": "PulseLab", "role": "Aferição de medidores"},
    {"code": "vision", "name": "DSYSTEM VISION", "role": "Gestão inteligente para óticas"},
    {"code": "bike", "name": "DSYSTEM BIKE", "role": "Oficinas de bicicletas"},
    {"code": "retail", "name": "DSYSTEM RETAIL", "role": "Gestão inteligente para o varejo; segmento controlado pelo HUB/API"},
    {"code": "vm", "name": "Gestor V&M", "role": "Vidros e mármore"},
    {"code": "inventario", "name": "Inventário", "role": "Inventário e relatórios"},
    {"code": "winthor_tools", "name": "WinThor Tools", "role": "Automações WinThor/Oracle"},
]


GLOBAL_PLANS = [
    {"code": "TRIAL", "name": "Teste", "scope": "GLOBAL", "status_default": "TRIAL"},
    {"code": "STARTER", "name": "Inicial", "scope": "GLOBAL", "status_default": "ACTIVE"},
    {"code": "BASIC", "name": "Básico", "scope": "GLOBAL", "status_default": "ACTIVE"},
    {"code": "PRO", "name": "Profissional", "scope": "GLOBAL", "status_default": "ACTIVE"},
    {"code": "BUSINESS", "name": "Empresarial", "scope": "GLOBAL", "status_default": "ACTIVE"},
    {"code": "ENTERPRISE", "name": "Enterprise", "scope": "GLOBAL", "status_default": "ACTIVE"},
]

PLAN_STATUSES = ["TRIAL", "ACTIVE", "SUSPENDED", "CANCELLED", "EXPIRED"]

@router.get("/official-standards")
def official_standards():
    settings = get_settings()
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "purpose": "Padrão oficial inicial para unificar DSYSTEM, ramificações, painel HUB e APIs antigas.",
        "default_company": {
            "name": settings.default_company_name,
            "slug": settings.default_company_slug,
        },
        "default_login_for_local_test": {
            "username": settings.master_username,
            "password": settings.master_password,
            "company_slug": settings.default_company_slug,
            "warning": "Trocar usuário/senha/chave secreta antes de produção.",
        },
        "auth_header_format": "Bearer <access_token>",
        "official_modules": OFFICIAL_MODULES,
        "integration_order": [
            "Finalizar API CORE",
            "Adaptar DS STUDIO GO",
            "Adaptar DSYSTEM AR",
            "Adaptar DSYSTEM-AR-PAINEL",
            "Adaptar DSYSTEM STUDIO Desktop",
            "Conectar DSYSTEM HUB",
        ],
        "sync_identity_rule": {
            "anti_duplicate_key": "company_id + module_code + external_id",
            "soft_delete": "is_deleted=true + deleted_at",
            "do_not_delete_when_api_empty": True,
        },
        "global_plan_rule": {
            "plans_are_global": True,
            "applies_to_all_products": True,
            "controlled_by": "DSYSTEM HUB / DSYSTEM SERVER CORE",
            "plans": GLOBAL_PLANS,
            "statuses": PLAN_STATUSES,
            "hub_can": ["activate", "change_plan", "start_trial", "suspend", "cancel", "expire"],
        },
        "retail_rule": {
            "product_code": "retail",
            "commercial_name": "DSYSTEM RETAIL — Gestão inteligente para o varejo.",
            "client_can_choose_segment": False,
            "configured_by": "DSYSTEM HUB / DSYSTEM SERVER CORE",
            "segments": ["MARKET", "CONVENIENCE", "CONSTRUCTION", "GENERAL_STORE"],
        },
    }


@router.get("/plan-standards")
def plan_standards():
    return {
        "version": get_settings().app_version,
        "rule": "Planos são globais e podem ser aplicados a qualquer produto do ecossistema DSYSTEM.",
        "controlled_by": "DSYSTEM HUB / DSYSTEM SERVER CORE",
        "plans": GLOBAL_PLANS,
        "statuses": PLAN_STATUSES,
        "applies_to": [m["code"] for m in OFFICIAL_MODULES],
        "hub_actions": {
            "trial": "ativar plano de teste com data inicial/final",
            "activate": "ativar produto/plano",
            "change": "trocar plano a qualquer momento",
            "suspend": "suspender acesso temporariamente",
            "cancel": "cancelar produto contratado",
            "expire": "marcar plano como expirado",
        },
    }


@router.get("/integration-map")
def integration_map():
    return {
        "hub": "DSYSTEM HUB consome a DSYSTEM SERVER CORE API para controle geral.",
        "core": "DSYSTEM SERVER CORE centraliza login, empresas, usuários, módulos, sync e logs.",
        "current_existing_systems_to_migrate_later": [
            "DS STUDIO GO",
            "DSYSTEM STUDIO",
            "DSYSTEM AR",
            "DSYSTEM-AR-PAINEL",
        ],
        "future_modules": ["PulseLab", "DSYSTEM VISION", "DSYSTEM BIKE", "DSYSTEM RETAIL", "Gestor V&M"],
    }

@router.get("/security-standards")
def security_standards():
    return {
        "version": get_settings().app_version,
        "purpose": "Padrão inicial de segurança, perfis e permissões do DSYSTEM SERVER CORE.",
        "official_roles": ROLE_STANDARDS,
        "auth": {
            "type": "Bearer token",
            "header": "Authorization: Bearer <access_token>",
            "default_local_login": {
                "username": get_settings().master_username,
                "password": get_settings().master_password,
                "company_slug": get_settings().default_company_slug,
            },
        },
        "production_pending_items": [
            "Trocar SECRET_KEY",
            "Usar PostgreSQL",
            "Ativar HTTPS",
            "Definir CORS por domínio",
            "Criar política de senha forte",
            "Criar refresh token nas próximas versões",
            "Criar backup automático",
        ],
    }
