"""Admin user management.

Bất biến bảo mật (xem docs/architecture.md D23, D24, D25):
- Actor chỉ thao tác trên user cùng organization.
- Actor chỉ assign role có permissions ⊆ permissions của actor.
- Không xóa chính mình.
- Không xóa SUPER_ADMIN cuối cùng.
- Không xóa cứng — chỉ soft delete (is_active=False).
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_rbac import get_user_permissions, get_user_role_ids
from app.models.user import User
from app.repositories.audit_repo import AuditRepository
from app.repositories.refresh_token_repo import RefreshTokenRepository
from app.repositories.role_repo import RoleRepository
from app.repositories.session_repo import SessionRepository
from app.repositories.user_repo import UserRepository
from app.security.password import hash_password


class UserAdminService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.roles = RoleRepository(db)
        self.sessions = SessionRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)
        self.audit = AuditRepository(db)

    # ---------- Create ----------

    async def create_user(
        self,
        *,
        actor: User,
        email: str,
        password: str,
        full_name: str | None,
        role_ids: list[UUID],
        is_active: bool,
        ip_address: str | None,
        user_agent: str | None,
    ) -> User:
        existing = await self.users.get_by_email(actor.organization_id, email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists in this organization",
            )

        # Validate roles trước khi tạo user
        await self._validate_roles_assignable(actor, role_ids)

        user = User(
            organization_id=actor.organization_id,
            email=email.lower(),
            full_name=full_name,
            password_hash=hash_password(password),
            is_active=is_active,
        )
        await self.users.create(user)

        if role_ids:
            await self.users.set_roles(user.id, role_ids)

        await self.audit.insert(
            organization_id=actor.organization_id,
            actor_id=actor.id,
            action="user.create",
            resource_type="user",
            resource_id=str(user.id),
            ip_address=ip_address,
            user_agent=user_agent,
            outcome="success",
            metadata={"email": email, "role_ids": [str(r) for r in role_ids]},
        )
        return user

    # ---------- Update ----------

    async def update_user(
        self,
        *,
        actor: User,
        user_id: UUID,
        full_name: str | None,
        is_active: bool | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> User:
        target = await self._load_target_in_org(actor, user_id)

        changed: dict = {}
        if full_name is not None and full_name != target.full_name:
            target.full_name = full_name
            changed["full_name"] = full_name
        if is_active is not None and is_active != target.is_active:
            if not is_active and target.id == actor.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot deactivate yourself",
                )
            if not is_active:
                await self._ensure_not_last_super_admin(actor, target)
            target.is_active = is_active
            changed["is_active"] = is_active
            if not is_active:
                await self.sessions.revoke_all_for_user(target.id)
                await self.refresh_tokens.revoke_all_for_user(target.id)
                await self.audit.insert(
                    organization_id=actor.organization_id,
                    actor_id=actor.id,
                    action="user.deactivate",
                    resource_type="user",
                    resource_id=str(target.id),
                    ip_address=ip_address,
                    user_agent=user_agent,
                    outcome="success",
                    metadata={},
                )
            else:
                await self.audit.insert(
                    organization_id=actor.organization_id,
                    actor_id=actor.id,
                    action="user.activate",
                    resource_type="user",
                    resource_id=str(target.id),
                    ip_address=ip_address,
                    user_agent=user_agent,
                    outcome="success",
                    metadata={},
                )

        await self.audit.insert(
            organization_id=actor.organization_id,
            actor_id=actor.id,
            action="user.update",
            resource_type="user",
            resource_id=str(target.id),
            ip_address=ip_address,
            user_agent=user_agent,
            outcome="success",
            metadata={"changed": changed},
        )
        return target

    # ---------- Delete (soft) ----------

    async def delete_user(
        self,
        *,
        actor: User,
        user_id: UUID,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        target = await self._load_target_in_org(actor, user_id)
        if target.id == actor.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete yourself",
            )
        await self._ensure_not_last_super_admin(actor, target)

        target.is_active = False
        await self.sessions.revoke_all_for_user(target.id)
        await self.refresh_tokens.revoke_all_for_user(target.id)
        await self.audit.insert(
            organization_id=actor.organization_id,
            actor_id=actor.id,
            action="user.delete",
            resource_type="user",
            resource_id=str(target.id),
            ip_address=ip_address,
            user_agent=user_agent,
            outcome="success",
            metadata={"email": target.email},
        )

    # ---------- Set roles ----------

    async def set_roles(
        self,
        *,
        actor: User,
        user_id: UUID,
        role_ids: list[UUID],
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        target = await self._load_target_in_org(actor, user_id)
        await self._validate_roles_assignable(actor, role_ids)

        # Không cho actor tự revoke SUPER_ADMIN của chính mình nếu là cuối cùng
        if target.id == actor.id:
            current_role_ids = await get_user_role_ids(actor, self.db)
            super_admin_role = await self.roles.get_by_name(
                actor.organization_id, "SUPER_ADMIN"
            )
            if super_admin_role and super_admin_role.id in current_role_ids:
                if super_admin_role.id not in role_ids:
                    await self._ensure_not_last_super_admin(actor, target)

        previous = await self.users.get_role_names(target.id)
        await self.users.set_roles(target.id, role_ids)
        new_roles = await self.users.get_role_names(target.id)

        assigned = set(new_roles) - set(previous)
        revoked = set(previous) - set(new_roles)

        if assigned:
            await self.audit.insert(
                organization_id=actor.organization_id,
                actor_id=actor.id,
                action="user.roles.assign",
                resource_type="user",
                resource_id=str(target.id),
                ip_address=ip_address,
                user_agent=user_agent,
                outcome="success",
                metadata={"roles": sorted(assigned)},
            )
        if revoked:
            await self.audit.insert(
                organization_id=actor.organization_id,
                actor_id=actor.id,
                action="user.roles.revoke",
                resource_type="user",
                resource_id=str(target.id),
                ip_address=ip_address,
                user_agent=user_agent,
                outcome="success",
                metadata={"roles": sorted(revoked)},
            )

    # ---------- Revoke sessions ----------

    async def revoke_sessions(
        self,
        *,
        actor: User,
        user_id: UUID,
        ip_address: str | None,
        user_agent: str | None,
    ) -> int:
        target = await self._load_target_in_org(actor, user_id)
        await self.sessions.revoke_all_for_user(target.id)
        count = await self.refresh_tokens.revoke_all_for_user(target.id)
        await self.audit.insert(
            organization_id=actor.organization_id,
            actor_id=actor.id,
            action="session.revoke",
            resource_type="user",
            resource_id=str(target.id),
            ip_address=ip_address,
            user_agent=user_agent,
            outcome="success",
            metadata={"revoked_tokens": count},
        )
        return count

    # ---------- helpers ----------

    async def _load_target_in_org(self, actor: User, user_id: UUID) -> User:
        target = await self.users.get_by_id_for_update(user_id)
        # 404 thay vì 403 để không lộ user tồn tại ở org khác
        if target is None or target.organization_id != actor.organization_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return target

    async def _validate_roles_assignable(
        self, actor: User, role_ids: list[UUID]
    ) -> None:
        """Mọi role phải cùng org + permissions ⊆ permissions của actor."""
        if not role_ids:
            return
        actor_perms = await get_user_permissions(actor, self.db)
        for rid in role_ids:
            role = await self.roles.get_by_id(rid, actor.organization_id)
            if role is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Role {rid} not found in your organization",
                )
            role_perms = {p.code for p in await self.roles.get_permissions(rid)}
            if not role_perms.issubset(actor_perms):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        f"Cannot assign role '{role.name}': it has permissions "
                        f"you don't have: {sorted(role_perms - actor_perms)}"
                    ),
                )

    async def _ensure_not_last_super_admin(
        self, actor: User, target: User
    ) -> None:
        target_roles = await self.users.get_role_names(target.id)
        if "SUPER_ADMIN" not in target_roles:
            return
        count = await self.users.count_super_admins(actor.organization_id)
        if count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last SUPER_ADMIN",
            )
