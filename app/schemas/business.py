from typing import Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.common import ORMBase


class SyncItem(BaseModel):
    """Item flexível para receber dados vindos dos sistemas locais.

    Campos conhecidos são normalizados; campos extras são preservados em raw_payload.
    """
    model_config = ConfigDict(extra="allow")

    external_id: str | int | None = None
    id: str | int | None = None
    local_id: str | int | None = None
    module_code: str | None = None
    sync_source: str | None = None
    is_deleted: bool | None = None
    deleted_at: datetime | None = None
    created_at: str | None = None
    updated_at: str | None = None


class SyncBatchRequest(BaseModel):
    module_code: str = "studio"
    sync_source: str = "desktop_sync"
    items: list[dict[str, Any]] = Field(default_factory=list)


class SyncBatchResponse(BaseModel):
    ok: bool
    entity: str
    module_code: str
    sync_source: str
    total_received: int
    total_created: int
    total_updated: int
    total_ignored: int
    total_errors: int
    sync_log_id: int
    message: str


class CustomerResponse(ORMBase):
    id: int
    company_id: int
    module_code: str
    external_id: str
    sync_source: str
    name: str
    phone: str | None = None
    email: str | None = None
    document: str | None = None
    notes: str | None = None
    is_deleted: bool
    deleted_at: datetime | None = None


class AppointmentResponse(ORMBase):
    id: int
    company_id: int
    module_code: str
    external_id: str
    sync_source: str
    customer_external_id: str | None = None
    customer_name: str | None = None
    professional_name: str | None = None
    service_name: str | None = None
    start_at: str | None = None
    end_at: str | None = None
    status: str | None = None
    notes: str | None = None
    is_deleted: bool
    deleted_at: datetime | None = None


class TransactionResponse(ORMBase):
    id: int
    company_id: int
    module_code: str
    external_id: str
    sync_source: str
    transaction_type: str
    description: str
    amount: float
    category: str | None = None
    payment_method: str | None = None
    transaction_date: str | None = None
    customer_external_id: str | None = None
    customer_name: str | None = None
    notes: str | None = None
    is_deleted: bool
    deleted_at: datetime | None = None
