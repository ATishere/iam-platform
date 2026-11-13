"""Admin audit log query (Phase 4, D37)."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_rbac import require
from app.db.session import get_db
from app.models.user import User
from app.schemas.audit import AuditLogListResponse
from app.security.permissions import Permission
from app.services.audit_service import AuditService, to_read

router = APIRouter(prefix="/admin", tags=["admin:audit"])


@router.get("/audit-logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    action: str | None = Query(None, max_length=64),
    actor_id: UUID | None = Query(None),
    resource_type: str | None = Query(None, max_length=64),
    resource_id: str | None = Query(None, max_length=64),
    outcome: str | None = Query(None, max_length=16),
    from_date: datetime | None = Query(None),
    to_date: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require(Permission.AUDIT_READ)),
) -> AuditLogListResponse:
    svc = AuditService(db)
    rows, total = await svc.query_logs(
        organization_id=actor.organization_id,
        action=action,
        actor_id=actor_id,
        resource_type=resource_type,
        resource_id=resource_id,
        outcome=outcome,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )
    return AuditLogListResponse(
        items=[to_read(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )
