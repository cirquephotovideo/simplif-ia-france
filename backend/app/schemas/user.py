from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr
from ..models.user import UserRole, UserPlan


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    plan: UserPlan
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: datetime | None = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    profile: dict | None = None
