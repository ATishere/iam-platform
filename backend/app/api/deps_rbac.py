"""RBAC dependencies.

Cách dùng:
    @router.get(..., dependencies=[Depends(require(Permission.USERS_READ))])

    # Hoặc cần actor trong handler:
    actor: User = Depends(require(Permission.USERS_CREATE))

`require` trả về User (actor) để route dùng tiếp. Không cache permissions
ở Phase 3 — load từ DB mỗi request.
"""

from collections.abc import Callable
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.permission import Permission as PermissionModel
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.user_role import UserRole


async def get_user_permissions(
    user: User, db: AsyncSession
) -> frozenset[str]:
    """Trả về tập permission codes của user trong org của user."""
    stmt = (
        select(PermissionModel.code)
        .join(RolePermission, RolePermission.permission_id == PermissionModel.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(
            UserRole.user_id == user.id,
            Role.organization_id == user.organization_id,
        )
    )
    rows = (await db.execute(stmt)).scalars().all()
    return frozenset(rows)


async def get_user_role_ids(user: User, db: AsyncSession) -> frozenset[UUID]:
    stmt = select(UserRole.role_id).where(UserRole.user_id == user.id)
    rows = (await db.execute(stmt)).scalars().all()
    return frozenset(rows)


def require(*required: str) -> Callable:
    """User phải có TẤT CẢ permissions. Trả về actor."""
    if not required:
        raise ValueError("require() cần ít nhất 1 permission")

    async def _dep(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        perms = await get_user_permissions(user, db)
        missing = set(required) - perms
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {sorted(missing)}",
            )
        return user

    return _dep


def require_any(*required: str) -> Callable:
    """User phải có ÍT NHẤT 1 permission. Trả về actor."""
    if not required:
        raise ValueError("require_any() cần ít nhất 1 permission")

    async def _dep(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        perms = await get_user_permissions(user, db)
        if not (perms & set(required)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {sorted(required)}",
            )
        return user

    return _dep
