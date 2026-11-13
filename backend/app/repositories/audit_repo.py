"""Audit repository: append-only insert + query (Phase 4).

`insert` là đường ghi duy nhất; `query`/`query_in_actions` chỉ đọc.
Không expose update/delete (D7).
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.security.audit import redact


class AuditRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def insert(
        self,
        *,
        organization_id,
        actor_id,
        action: str,
        resource_type: str | None,
        resource_id: str | None,
        ip_address: str | None,
        user_agent: str | None,
        outcome: str,
        metadata: dict | None,
    ) -> AuditLog:
        log = AuditLog(
            organization_id=organization_id,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            outcome=outcome,
            metadata_=redact(metadata or {}),
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def query(
        self,
        *,
        organization_id: UUID,
        action: str | None = None,
        actor_id: UUID | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        outcome: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AuditLog], int]:
        filters = [AuditLog.organization_id == organization_id]
        if action is not None:
            filters.append(AuditLog.action == action)
        if actor_id is not None:
            filters.append(AuditLog.actor_id == actor_id)
        if resource_type is not None:
            filters.append(AuditLog.resource_type == resource_type)
        if resource_id is not None:
            filters.append(AuditLog.resource_id == resource_id)
        if outcome is not None:
            filters.append(AuditLog.outcome == outcome)
        if from_date is not None:
            filters.append(AuditLog.created_at >= from_date)
        if to_date is not None:
            filters.append(AuditLog.created_at <= to_date)

        total = (
            await self.db.execute(
                select(func.count()).select_from(AuditLog).where(*filters)
            )
        ).scalar_one()
        stmt = (
            select(AuditLog)
            .where(*filters)
            .order_by(AuditLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self.db.execute(stmt)).scalars().all()
        return list(rows), int(total)

    async def query_in_actions(
        self,
        *,
        organization_id: UUID,
        actions: frozenset[str],
        actor_id: UUID | None = None,
        outcome: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AuditLog], int]:
        filters = [
            AuditLog.organization_id == organization_id,
            AuditLog.action.in_(sorted(actions)),
        ]
        if actor_id is not None:
            filters.append(AuditLog.actor_id == actor_id)
        if outcome is not None:
            filters.append(AuditLog.outcome == outcome)
        if from_date is not None:
            filters.append(AuditLog.created_at >= from_date)
        if to_date is not None:
            filters.append(AuditLog.created_at <= to_date)

        total = (
            await self.db.execute(
                select(func.count()).select_from(AuditLog).where(*filters)
            )
        ).scalar_one()
        stmt = (
            select(AuditLog)
            .where(*filters)
            .order_by(AuditLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self.db.execute(stmt)).scalars().all()
        return list(rows), int(total)
