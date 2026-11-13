from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permission import Permission


class PermissionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_all(self) -> list[Permission]:
        stmt = select(Permission).order_by(Permission.code.asc())
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_by_code(self, code: str) -> Permission | None:
        stmt = select(Permission).where(Permission.code == code)
        return (await self.db.execute(stmt)).scalar_one_or_none()
