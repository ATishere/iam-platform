from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RecentSecurityEvent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    action: str
    actor_id: UUID | None
    outcome: str
    created_at: datetime


class DashboardStats(BaseModel):
    users_total: int
    users_active: int
    users_locked: int
    recent_logins_24h: int
    failed_logins_24h: int
    recent_security_events: list[RecentSecurityEvent]
