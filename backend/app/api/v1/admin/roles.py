from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import client_ip, client_user_agent
from app.api.deps_rbac import require
from app.db.session import get_db
from app.models.role import Role
from app.models.user import User
from app.repositories.role_repo import RoleRepository
from app.schemas.admin import RoleCreate, RoleListResponse, RoleRead, RoleUpdate
from app.security.permissions import Permission
from app.services.role_service import RoleService

router = APIRouter(prefix="/admin/roles", tags=["admin:roles"])


async def _to_read(role: Role, roles_repo: RoleRepository) -> RoleRead:
    perms = await roles_repo.get_permissions(role.id)
    dto = RoleRead.model_validate(role)
    dto.permission_codes = sorted(p.code for p in perms)
    return dto


@router.get("", response_model=RoleListResponse)
async def list_roles(
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require(Permission.ROLES_READ)),
) -> RoleListResponse:
    svc = RoleService(db)
    roles_repo = RoleRepository(db)
    roles = await svc.list_roles(actor)
    items = [await _to_read(r, roles_repo) for r in roles]
    return RoleListResponse(items=items, total=len(items))


@router.post("", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(
    body: RoleCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require(Permission.ROLES_MANAGE)),
) -> RoleRead:
    svc = RoleService(db)
    roles_repo = RoleRepository(db)
    try:
        role = await svc.create_role(
            actor=actor,
            name=body.name,
            description=body.description,
            permission_codes=body.permission_codes,
            ip_address=client_ip(request),
            user_agent=client_user_agent(request),
        )
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    return await _to_read(role, roles_repo)


@router.patch("/{role_id}", response_model=RoleRead)
async def update_role(
    role_id: UUID,
    body: RoleUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require(Permission.ROLES_MANAGE)),
) -> RoleRead:
    svc = RoleService(db)
    roles_repo = RoleRepository(db)
    try:
        role = await svc.update_role(
            actor=actor,
            role_id=role_id,
            description=body.description,
            ip_address=client_ip(request),
            user_agent=client_user_agent(request),
        )
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    return await _to_read(role, roles_repo)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require(Permission.ROLES_MANAGE)),
) -> None:
    svc = RoleService(db)
    try:
        await svc.delete_role(
            actor=actor,
            role_id=role_id,
            ip_address=client_ip(request),
            user_agent=client_user_agent(request),
        )
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
