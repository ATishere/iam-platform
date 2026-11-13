from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    email: EmailStr
    full_name: str | None
    is_active: bool
    is_locked: bool
    last_login_at: datetime | None
    created_at: datetime


class UserUpdateMe(BaseModel):
    full_name: str | None = Field(None, max_length=255)


class MyPermissions(BaseModel):
    permissions: list[str]
