from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session


def _now() -> datetime:
    return datetime.now(timezone.utc)


class SessionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, session: Session) -> Session:
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_active(self, session_id: UUID) -> Session | None:
        stmt = select(Session).where(
            Session.id == session_id, Session.is_active.is_(True)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_by_id(self, session_id: UUID) -> Session | None:
        stmt = select(Session).where(Session.id == session_id)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def list_for_user(self, user_id: UUID) -> list[Session]:
        stmt = (
            select(Session)
            .where(Session.user_id == user_id, Session.is_active.is_(True))
            .order_by(Session.created_at.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def revoke(self, session_id: UUID) -> None:
        await self.db.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(is_active=False, revoked_at=_now())
        )

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        await self.db.execute(
            update(Session)
            .where(Session.user_id == user_id, Session.is_active.is_(True))
            .values(is_active=False, revoked_at=_now())
        )

    async def touch(self, session_id: UUID) -> None:
        await self.db.execute(
            update(Session).where(Session.id == session_id).values(last_seen_at=_now())
        )
