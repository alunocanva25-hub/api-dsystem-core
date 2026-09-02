from pydantic import BaseModel, EmailStr
from app.schemas.common import ORMBase


class UserCreate(BaseModel):
    company_id: int
    username: str
    full_name: str
    password: str
    email: EmailStr | None = None
    role: str = "USER"


class UserResponse(ORMBase):
    id: int
    company_id: int
    username: str
    full_name: str
    email: str | None = None
    role: str
    is_active: bool
