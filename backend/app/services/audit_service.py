"""Audit query + security events (Phase 4, D37–D39)."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status

from app.models.audit_log import AuditLog
from app.repositories.audit_repo import AuditRepository
from app.schemas.audit import AuditLogRead

# Chỉ các action liên quan auth/session mới thuộc "security events".
_SECURITY_ACTIONS: frozenset[str] = frozenset(
    {
        "login.success",
        "login.failure",
        "login.locked",
        "logout",
        "auth.logout_all",
        "refresh.success",
        "refresh.expired",
        "refresh.reuse_detected",
        "password.change.success",
        "password.change.failure",
        "password.reset.requested",
        "password.reset.invalid",
        "password.reset.success",
        "register.success",
        "session.revoke",
        "security.ratelimit_exceeded",
    }
)


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


_MAX_RANGE_DAYS = 90


def _validate_range(
    from_date: datetime | None, to_date: datetime | None
) -> tuple[datetime | None, datetime | None]:
    start, end = _as_utc(from_date), _as_utc(to_date)
    if start is not None and end is not None:
        if start > end:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="from_date must be before or equal to to_date",
            )
        if (end - start).days > _MAX_RANGE_DAYS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Date range must not exceed {_MAX_RANGE_DAYS} days",
            )
    return start, end


def to_read(log: AuditLog) -> AuditLogRead:
    return AuditLogRead(
        id=log.id,
        organization_id=log.organization_id,
        actor_id=log.actor_id,
        action=log.action,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        outcome=log.outcome,
        metadata=log.metadata_ or {},
        created_at=log.created_at,
    )


class AuditService:
    def __init__(self, db) -> None:
        self.repo = AuditRepository(db)

    async def query_logs(
        self,
        *,
        organization_id: UUID,
        action: str | None,
        actor_id: UUID | None,
        resource_type: str | None,
        resource_id: str | None,
        outcome: str | None,
        from_date: datetime | None,
        to_date: datetime | None,
        page: int,
        page_size: int,
    ) -> tuple[list[AuditLog], int]:
        start, end = _validate_range(from_date, to_date)
        return await self.repo.query(
            organization_id=organization_id,
            action=action,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            from_date=start,
            to_date=end,
            page=page,
            page_size=page_size,
        )

    async def query_security_events(
        self,
        *,
        organization_id: UUID,
        action: str | None,
        outcome: str | None,
        from_date: datetime | None,
        to_date: datetime | None,
        page: int,
        page_size: int,
    ) -> tuple[list[AuditLog], int]:
        start, end = _validate_range(from_date, to_date)
        if action is not None and action not in _SECURITY_ACTIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"'{action}' is not a security event action",
            )
        if action is not None:
            return await self.repo.query(
                organization_id=organization_id,
                action=action,
                outcome=outcome,
                from_date=start,
                to_date=end,
                page=page,
                page_size=page_size,
            )
        return await self.repo.query_in_actions(
            organization_id=organization_id,
            actions=_SECURITY_ACTIONS,
            outcome=outcome,
            from_date=start,
            to_date=end,
            page=page,
            page_size=page_size,
        )
