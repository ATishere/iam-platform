from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user_role import UserRole


class RoleRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(
        self, role_id: UUID, organization_id: UUID | None = None
    ) -> Role | None:
        stmt = select(Role).where(Role.id == role_id)
        if organization_id is not None:
            stmt = stmt.where(Role.organization_id == organization_id)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_by_name(
        self, organization_id: UUID, name: str
    ) -> Role | None:
        stmt = select(Role).where(
            Role.organization_id == organization_id, Role.name == name
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def list_by_org(self, organization_id: UUID) -> list[Role]:
        stmt = (
            select(Role)
            .where(Role.organization_id == organization_id)
            .order_by(Role.name.asc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def create(self, role: Role) -> Role:
        self.db.add(role)
        await self.db.flush()
        return role

    async def delete(self, role: Role) -> None:
        await self.db.delete(role)

    async def get_permissions(self, role_id: UUID) -> list[Permission]:
        stmt = (
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def set_permissions(
        self, role_id: UUID, permission_ids: list[UUID]
    ) -> None:
        await self.db.execute(
            delete(RolePermission).where(RolePermission.role_id == role_id)
        )
        for pid in permission_ids:
            self.db.add(RolePermission(role_id=role_id, permission_id=pid))

    async def count_users(self, role_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(UserRole)
            .where(UserRole.role_id == role_id)
        )
        return (await self.db.execute(stmt)).scalar_one()
