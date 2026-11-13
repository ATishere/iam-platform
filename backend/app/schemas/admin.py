from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- Pagination ---

class PageMeta(BaseModel):
    total: int
    page: int
    page_size: int


# --- Users ---

class UserAdminRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    email: EmailStr
    full_name: str | None
    is_active: bool
    is_locked: bool
    failed_login_attempts: int
    locked_until: datetime | None
    last_login_at: datetime | None
    created_at: datetime
    roles: list[str] = []


class UserAdminCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=128)
    full_name: str | None = Field(None, max_length=255)
    role_ids: list[UUID] = Field(default_factory=list)
    is_active: bool = True


class UserAdminUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=255)
    is_active: bool | None = None


class UserSetRolesRequest(BaseModel):
    role_ids: list[UUID]


class UserAdminListResponse(BaseModel):
    items: list[UserAdminRead]
    total: int
    page: int
    page_size: int


# --- Roles ---

class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    description: str | None
    is_system: bool
    created_at: datetime
    permission_codes: list[str] = []


class RoleCreate(BaseModel):
    name: str = Field(
        ..., min_length=2, max_length=64, pattern=r"^[A-Z][A-Z0-9_]*$"
    )
    description: str | None = Field(None, max_length=255)
    permission_codes: list[str] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    description: str | None = Field(None, max_length=255)


class RoleListResponse(BaseModel):
    items: list[RoleRead]
    total: int


# --- Permissions ---

class PermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    description: str | None


class PermissionListResponse(BaseModel):
    items: list[PermissionRead]
    total: int
