"""Serviço central de permissões do DSYSTEM SERVER CORE.

V1.0.0.8 cria uma matriz inicial simples, preparada para evoluir por
produto, módulo e empresa sem quebrar os clientes já integrados.
"""
from __future__ import annotations

from typing import Any

ROLE_STANDARDS: dict[str, dict[str, Any]] = {
    "MASTER": {
        "label": "Master DSYSTEM",
        "description": "Controle total do ecossistema, empresas, usuários, módulos, produtos e logs.",
        "level": 100,
        "permissions": {
            "admin.companies.read": True,
            "admin.companies.write": True,
            "admin.users.read": True,
            "admin.users.write": True,
            "admin.modules.write": True,
            "admin.products.write": True,
            "admin.logs.read": True,
            "audit.read": True,
            "sync.read": True,
            "sync.write": True,
            "hub.access": True,
            "core.settings.write": True,
        },
    },
    "ADMIN": {
        "label": "Administrador da Empresa",
        "description": "Administra usuários e módulos da própria empresa, sem controle global do CORE.",
        "level": 80,
        "permissions": {
            "admin.companies.read": True,
            "admin.companies.write": False,
            "admin.users.read": True,
            "admin.users.write": True,
            "admin.modules.write": True,
            "admin.products.write": False,
            "admin.logs.read": True,
            "audit.read": True,
            "sync.read": True,
            "sync.write": True,
            "hub.access": True,
            "core.settings.write": False,
        },
    },
    "MANAGER": {
        "label": "Gerente",
        "description": "Consulta e opera dados da empresa; pode acompanhar relatórios e sincronizações.",
        "level": 60,
        "permissions": {
            "admin.companies.read": False,
            "admin.companies.write": False,
            "admin.users.read": True,
            "admin.users.write": False,
            "admin.modules.write": False,
            "admin.products.write": False,
            "admin.logs.read": True,
            "audit.read": False,
            "sync.read": True,
            "sync.write": True,
            "hub.access": False,
            "core.settings.write": False,
        },
    },
    "OPERATOR": {
        "label": "Operador",
        "description": "Usa os módulos liberados e envia/recebe sincronizações operacionais.",
        "level": 40,
        "permissions": {
            "admin.companies.read": False,
            "admin.companies.write": False,
            "admin.users.read": False,
            "admin.users.write": False,
            "admin.modules.write": False,
            "admin.products.write": False,
            "admin.logs.read": False,
            "audit.read": False,
            "sync.read": True,
            "sync.write": True,
            "hub.access": False,
            "core.settings.write": False,
        },
    },
    "VIEWER": {
        "label": "Visualizador",
        "description": "Acesso somente leitura aos módulos liberados.",
        "level": 20,
        "permissions": {
            "admin.companies.read": False,
            "admin.companies.write": False,
            "admin.users.read": False,
            "admin.users.write": False,
            "admin.modules.write": False,
            "admin.products.write": False,
            "admin.logs.read": False,
            "audit.read": False,
            "sync.read": True,
            "sync.write": False,
            "hub.access": False,
            "core.settings.write": False,
        },
    },
}


def normalize_role(role: str | None) -> str:
    role = (role or "VIEWER").upper().strip()
    if role == "USER":
        return "OPERATOR"
    return role if role in ROLE_STANDARDS else "VIEWER"


def build_permissions(role: str | None, modules: list[dict]) -> dict[str, Any]:
    role_key = normalize_role(role)
    base = ROLE_STANDARDS[role_key]
    module_codes = [m["code"] for m in modules]
    permissions = dict(base["permissions"])
    return {
        "role": role_key,
        "role_label": base["label"],
        "role_level": base["level"],
        "can_manage_companies": permissions.get("admin.companies.write", False),
        "can_manage_users": permissions.get("admin.users.write", False),
        "can_manage_modules": permissions.get("admin.modules.write", False),
        "can_view_audit": permissions.get("audit.read", False),
        "can_sync": permissions.get("sync.write", False) or permissions.get("sync.read", False),
        "enabled_module_codes": module_codes,
        "rules": permissions,
    }
