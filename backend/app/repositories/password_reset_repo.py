from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.password_reset_token import PasswordResetToken


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PasswordResetRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, token: PasswordResetToken) -> PasswordResetToken:
        self.db.add(token)
        await self.db.flush()
        return token

    async def get_by_hash_for_update(self, token_hash: str) -> PasswordResetToken | None:
        stmt = (
            select(PasswordResetToken)
            .where(PasswordResetToken.token_hash == token_hash)
            .with_for_update()
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def mark_used(self, token_id: UUID) -> None:
        await self.db.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.id == token_id)
            .values(used_at=_now())
        )

    async def invalidate_all_for_user(self, user_id: UUID) -> None:
        await self.db.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.used_at.is_(None),
            )
            .values(used_at=_now())
        )
