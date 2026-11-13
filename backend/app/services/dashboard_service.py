"""Dashboard aggregation. 6 query tuần tự, không concurrent (session
không thread-safe). Tổng ~10-20ms cho MVP."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.dashboard import DashboardStats, RecentSecurityEvent
from app.services.audit_service import _SECURITY_ACTIONS


class DashboardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_stats(self, *, organization_id: UUID) -> DashboardStats:
        now = datetime.now(timezone.utc)
        since = now - timedelta(hours=24)

        total = (
            await self.db.execute(
                select(func.count())
                .select_from(User)
                .where(User.organization_id == organization_id)
            )
        ).scalar_one()

        active = (
            await self.db.execute(
                select(func.count())
                .select_from(User)
                .where(
                    User.organization_id == organization_id,
                    User.is_active.is_(True),
                )
            )
        ).scalar_one()

        locked = (
            await self.db.execute(
                select(func.count())
                .select_from(User)
                .where(
                    User.organization_id == organization_id,
                    User.is_locked.is_(True),
                    User.locked_until.is_not(None),
                    User.locked_until > now,
                )
            )
        ).scalar_one()

        recent_logins = (
            await self.db.execute(
                select(func.count())
                .select_from(AuditLog)
                .where(
                    AuditLog.organization_id == organization_id,
                    AuditLog.action == "login.success",
                    AuditLog.created_at >= since,
                )
            )
        ).scalar_one()

        failed_logins = (
            await self.db.execute(
                select(func.count())
                .select_from(AuditLog)
                .where(
                    AuditLog.organization_id == organization_id,
                    AuditLog.action == "login.failure",
                    AuditLog.created_at >= since,
                )
            )
        ).scalar_one()

        rows = (
            (
                await self.db.execute(
                    select(AuditLog)
                    .where(
                        AuditLog.organization_id == organization_id,
                        AuditLog.action.in_(sorted(_SECURITY_ACTIONS)),
                    )
                    .order_by(AuditLog.created_at.desc())
                    .limit(5)
                )
            )
            .scalars()
            .all()
        )

        events = [RecentSecurityEvent.model_validate(row) for row in rows]

        return DashboardStats(
            users_total=total,
            users_active=active,
            users_locked=locked,
            recent_logins_24h=recent_logins,
            failed_logins_24h=failed_logins,
            recent_security_events=events,
        )
