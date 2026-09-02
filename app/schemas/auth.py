from pydantic import BaseModel
from app.schemas.common import ORMBase


class LoginRequest(BaseModel):
    username: str
    password: str
    company_slug: str | None = None


class CompanyContext(BaseModel):
    id: int
    name: str
    slug: str
    document: str | None = None
    is_active: bool


class ModuleContext(BaseModel):
    id: int
    code: str
    name: str
    description: str | None = None
    plan: str
    is_enabled: bool


class PermissionContext(BaseModel):
    role: str
    role_label: str | None = None
    role_level: int | None = None
    can_manage_companies: bool
    can_manage_users: bool
    can_manage_modules: bool
    can_view_audit: bool
    can_sync: bool
    enabled_module_codes: list[str]
    rules: dict[str, bool] = {}


class UserSession(BaseModel):
    id: int
    company_id: int
    username: str
    full_name: str
    email: str | None = None
    role: str
    is_active: bool
    company: CompanyContext | None = None
    modules: list[ModuleContext] = []
    permissions: PermissionContext


class TokenResponse(BaseModel):
    access_token: str
    token: str | None = None
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserSession
    company: CompanyContext | None = None
    modules: list[ModuleContext] = []
    ok: bool = True
    success: bool = True


class MeResponse(UserSession):
    pass


class TokenValidationResponse(BaseModel):
    ok: bool
    user: UserSession
