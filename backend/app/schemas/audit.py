"""Audit log read schemas (Phase 4)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AuditLogRead(BaseModel):
    id: UUID
    organization_id: UUID
    actor_id: UUID | None
    action: str
    resource_type: str | None
    resource_id: str | None
    ip_address: str | None
    user_agent: str | None
    outcome: str
    metadata: dict = Field(default_factory=dict)
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogRead]
    total: int
    page: int
    page_size: int
