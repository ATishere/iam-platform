from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import client_ip, client_user_agent
from app.api.deps_rbac import require
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.admin import (
    UserAdminCreate,
    UserAdminListResponse,
    UserAdminRead,
    UserAdminUpdate,
    UserSetRolesRequest,
)
from app.security.permissions import Permission
from app.services.user_admin_service import UserAdminService

router = APIRouter(prefix="/admin/users", tags=["admin:users"])


async def _to_read(user: User, db: AsyncSession) -> UserAdminRead:
    users = UserRepository(db)
    role_names = await users.get_role_names(user.id)
    # Build dict tường minh: user.roles là list[Role] ORM, không validate
    # trực tiếp được vào list[str] nếu dùng model_validate(user).
    return UserAdminRead.model_validate(
        {
            "id": user.id,
            "organization_id": user.organization_id,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_locked": user.is_locked,
            "failed_login_attempts": user.failed_login_attempts,
            "locked_until": user.locked_until,
            "last_login_at": user.last_login_at,
            "created_at": user.created_at,
            "roles": role_names,
        }
    )


@router.get("", response_model=UserAdminListResponse)
async def list_users(
    q: str | None = Query(None, max_length=100),
    is_active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require(Permission.USERS_READ)),
) -> UserAdminListResponse:
    users = UserRepository(db)
    rows, total = await users.list_paginated(
        organization_id=actor.organization_id,
        q=q,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )
    items = [await _to_read(u, db) for u in rows]
    return UserAdminListResponse(
        items=items, total=total, page=page, page_size=page_size
    )


@router.post(
    "", response_model=UserAdminRead, status_code=status.HTTP_201_CREATED
)
async def create_user(
    body: UserAdminCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require(Permission.USERS_CREATE)),
) -> UserAdminRead:
    svc = UserAdminService(db)
    try:
        user = await svc.create_user(
            actor=actor,
            email=body.email,
            password=body.password,
            full_name=body.full_name,
            role_ids=body.role_ids,
            is_active=body.is_active,
            ip_address=client_ip(request),
            user_agent=client_user_agent(request),
        )
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    return await _to_read(user, db)


@router.get("/{user_id}", response_model=UserAdminRead)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require(Permission.USERS_READ)),
) -> UserAdminRead:
    users = UserRepository(db)
    user = await users.get_by_id(user_id)
    if user is None or user.organization_id != actor.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return await _to_read(user, db)


@router.patch("/{user_id}", response_model=UserAdminRead)
async def update_user(
    user_id: UUID,
    body: UserAdminUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require(Permission.USERS_UPDATE)),
) -> UserAdminRead:
    svc = UserAdminService(db)
    try:
        user = await svc.update_user(
            actor=actor,
            user_id=user_id,
            full_name=body.full_name,
            is_active=body.is_active,
            ip_address=client_ip(request),
            user_agent=client_user_agent(request),
        )
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    return await _to_read(user, db)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require(Permission.USERS_DELETE)),
) -> None:
    svc = UserAdminService(db)
    try:
        await svc.delete_user(
            actor=actor,
            user_id=user_id,
            ip_address=client_ip(request),
            user_agent=client_user_agent(request),
        )
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise


@router.put("/{user_id}/roles", response_model=UserAdminRead)
async def set_user_roles(
    user_id: UUID,
    body: UserSetRolesRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require(Permission.USERS_UPDATE)),
) -> UserAdminRead:
    svc = UserAdminService(db)
    try:
        await svc.set_roles(
            actor=actor,
            user_id=user_id,
            role_ids=body.role_ids,
            ip_address=client_ip(request),
            user_agent=client_user_agent(request),
        )
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    users = UserRepository(db)
    user = await users.get_by_id(user_id)
    return await _to_read(user, db)


@router.delete("/{user_id}/sessions", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_user_sessions(
    user_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require(Permission.SESSIONS_REVOKE)),
) -> None:
    svc = UserAdminService(db)
    try:
        await svc.revoke_sessions(
            actor=actor,
            user_id=user_id,
            ip_address=client_ip(request),
            user_agent=client_user_agent(request),
        )
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
