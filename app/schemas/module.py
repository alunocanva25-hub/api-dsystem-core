from pydantic import BaseModel
from app.schemas.common import ORMBase


class ModuleResponse(ORMBase):
    id: int
    code: str
    name: str
    description: str | None = None
    is_active: bool


class CompanyModuleResponse(ORMBase):
    id: int
    company_id: int
    module_id: int
    plan: str
    is_enabled: bool
    module_code: str | None = None
    module_name: str | None = None


class EnableCompanyModuleRequest(BaseModel):
    company_id: int
    module_code: str
    plan: str = "default"


class DisableCompanyModuleRequest(BaseModel):
    company_id: int
    module_code: str
