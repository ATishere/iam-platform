from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_rbac import require
from app.db.session import get_db
from app.models.user import User
from app.repositories.permission_repo import PermissionRepository
from app.schemas.admin import PermissionListResponse, PermissionRead
from app.security.permissions import Permission

router = APIRouter(prefix="/admin/permissions", tags=["admin:permissions"])


@router.get("", response_model=PermissionListResponse)
async def list_permissions(
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require(Permission.ROLES_READ)),
) -> PermissionListResponse:
    repo = PermissionRepository(db)
    perms = await repo.list_all()
    return PermissionListResponse(
        items=[PermissionRead.model_validate(p) for p in perms],
        total=len(perms),
    )
