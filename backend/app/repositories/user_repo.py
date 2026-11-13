from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_email(
        self, organization_id: UUID, email: str
    ) -> User | None:
        stmt = select(User).where(
            User.organization_id == organization_id,
            User.email == email.lower(),
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_by_id_for_update(self, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id).with_for_update()
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        return user

    # ---------- Phase 3 ----------

    async def list_paginated(
        self,
        *,
        organization_id: UUID,
        q: str | None,
        is_active: bool | None,
        page: int,
        page_size: int,
    ) -> tuple[list[User], int]:
        base = select(User).where(User.organization_id == organization_id)
        count_base = select(func.count()).select_from(User).where(
            User.organization_id == organization_id
        )

        if q:
            pattern = f"%{q}%"
            cond = or_(User.email.ilike(pattern), User.full_name.ilike(pattern))
            base = base.where(cond)
            count_base = count_base.where(cond)

        if is_active is not None:
            base = base.where(User.is_active.is_(is_active))
            count_base = count_base.where(User.is_active.is_(is_active))

        total = (await self.db.execute(count_base)).scalar_one()
        rows = (
            await self.db.execute(
                base.order_by(User.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).scalars().all()
        return list(rows), total

    async def get_role_names(self, user_id: UUID) -> list[str]:
        stmt = (
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def count_super_admins(self, organization_id: UUID) -> int:
        """Đếm số user có role SUPER_ADMIN (để chặn xóa admin cuối cùng)."""
        stmt = (
            select(func.count(func.distinct(User.id)))
            .select_from(User)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(
                User.organization_id == organization_id,
                Role.name == "SUPER_ADMIN",
                User.is_active.is_(True),
            )
        )
        return (await self.db.execute(stmt)).scalar_one()

    async def set_roles(self, user_id: UUID, role_ids: list[UUID]) -> None:
        await self.db.execute(delete(UserRole).where(UserRole.user_id == user_id))
        for rid in role_ids:
            self.db.add(UserRole(user_id=user_id, role_id=rid))
        # Flush để get_role_names() ngay sau đó thấy đúng trạng thái mới
        # (session đang autoflush=False).
        await self.db.flush()
