from pydantic import BaseModel
from app.schemas.common import ORMBase


class CompanyCreate(BaseModel):
    name: str
    slug: str
    document: str | None = None


class CompanyResponse(ORMBase):
    id: int
    name: str
    document: str | None = None
    slug: str
    is_active: bool
