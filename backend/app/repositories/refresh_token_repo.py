from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


def _now() -> datetime:
    return datetime.now(timezone.utc)


class RefreshTokenRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, token: RefreshToken) -> RefreshToken:
        self.db.add(token)
        await self.db.flush()
        return token

    async def get_by_hash_for_update(self, token_hash: str) -> RefreshToken | None:
        """SELECT ... FOR UPDATE — bắt buộc cho reuse detection race."""
        stmt = (
            select(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .with_for_update()
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def revoke_family(self, family_id: UUID) -> int:
        result = await self.db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.family_id == family_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=_now())
        )
        return result.rowcount or 0

    async def revoke_all_for_session(self, session_id: UUID) -> int:
        result = await self.db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.session_id == session_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=_now())
        )
        return result.rowcount or 0

    async def revoke_all_for_user(self, user_id: UUID) -> int:
        result = await self.db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=_now())
        )
        return result.rowcount or 0

    async def mark_used_and_replace(
        self, old_id: UUID, new_id: UUID
    ) -> None:
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.id == old_id)
            .values(used_at=_now(), replaced_by_id=new_id)
        )
