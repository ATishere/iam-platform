from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_rbac import get_user_permissions
from app.models.role import Role
from app.models.user import User
from app.repositories.audit_repo import AuditRepository
from app.repositories.permission_repo import PermissionRepository
from app.repositories.role_repo import RoleRepository


class RoleService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.roles = RoleRepository(db)
        self.perms = PermissionRepository(db)
        self.audit = AuditRepository(db)

    async def list_roles(self, actor: User) -> list[Role]:
        return await self.roles.list_by_org(actor.organization_id)

    async def create_role(
        self,
        *,
        actor: User,
        name: str,
        description: str | None,
        permission_codes: list[str],
        ip_address: str | None,
        user_agent: str | None,
    ) -> Role:
        existing = await self.roles.get_by_name(actor.organization_id, name)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Role name already exists in this organization",
            )

        # Actor chỉ được tạo role với permissions ⊆ permissions của mình
        actor_perms = await get_user_permissions(actor, self.db)
        if not set(permission_codes).issubset(actor_perms):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Cannot create role with permissions you don't have: "
                    f"{sorted(set(permission_codes) - actor_perms)}"
                ),
            )

        # Resolve permission codes → ids
        perm_ids: list[UUID] = []
        for code in permission_codes:
            p = await self.perms.get_by_code(code)
            if p is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown permission code: {code}",
                )
            perm_ids.append(p.id)

        role = Role(
            organization_id=actor.organization_id,
            name=name,
            description=description,
            is_system=False,
        )
        await self.roles.create(role)
        if perm_ids:
            await self.roles.set_permissions(role.id, perm_ids)

        await self.audit.insert(
            organization_id=actor.organization_id,
            actor_id=actor.id,
            action="role.create",
            resource_type="role",
            resource_id=str(role.id),
            ip_address=ip_address,
            user_agent=user_agent,
            outcome="success",
            metadata={"name": name, "permissions": sorted(permission_codes)},
        )
        return role

    async def update_role(
        self,
        *,
        actor: User,
        role_id: UUID,
        description: str | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> Role:
        role = await self._load_role_in_org(actor, role_id)
        if description is not None:
            role.description = description
        await self.audit.insert(
            organization_id=actor.organization_id,
            actor_id=actor.id,
            action="role.update",
            resource_type="role",
            resource_id=str(role.id),
            ip_address=ip_address,
            user_agent=user_agent,
            outcome="success",
            metadata={"description": description},
        )
        return role

    async def delete_role(
        self,
        *,
        actor: User,
        role_id: UUID,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        role = await self._load_role_in_org(actor, role_id)
        if role.is_system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete a system role",
            )
        count = await self.roles.count_users(role.id)
        if count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Role is assigned to {count} user(s); revoke first",
            )
        await self.roles.delete(role)
        await self.audit.insert(
            organization_id=actor.organization_id,
            actor_id=actor.id,
            action="role.delete",
            resource_type="role",
            resource_id=str(role.id),
            ip_address=ip_address,
            user_agent=user_agent,
            outcome="success",
            metadata={"name": role.name},
        )

    async def _load_role_in_org(self, actor: User, role_id: UUID) -> Role:
        role = await self.roles.get_by_id(role_id, actor.organization_id)
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
            )
        return role
