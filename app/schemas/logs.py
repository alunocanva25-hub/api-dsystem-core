from pydantic import BaseModel
from app.schemas.common import ORMBase


class SyncLogCreate(BaseModel):
    company_id: int
    module_code: str
    direction: str
    status: str
    message: str | None = None
    total_received: int = 0
    total_created: int = 0
    total_updated: int = 0
    total_ignored: int = 0
    total_errors: int = 0


class SyncLogResponse(ORMBase):
    id: int
    company_id: int
    module_code: str
    direction: str
    status: str
    message: str | None = None
    total_received: int
    total_created: int
    total_updated: int
    total_ignored: int
    total_errors: int


class AuditLogResponse(ORMBase):
    id: int
    company_id: int | None = None
    user_id: int | None = None
    module_code: str | None = None
    action: str
    description: str | None = None
    ip_address: str | None = None
