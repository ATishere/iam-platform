from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.deps_rbac import get_user_permissions
from app.db.session import get_db
from app.models.user import User
from app.repositories.session_repo import SessionRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import SessionRead
from app.schemas.user import MyPermissions, UserRead, UserUpdateMe

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.get("/me/permissions", response_model=MyPermissions)
async def get_my_permissions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MyPermissions:
    perms = await get_user_permissions(current_user, db)
    return MyPermissions(permissions=sorted(perms))


@router.patch("/me", response_model=UserRead)
async def update_me(
    body: UserUpdateMe,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserRead:
    users = UserRepository(db)
    user = await users.get_by_id_for_update(current_user.id)
    if body.full_name is not None:
        user.full_name = body.full_name
    await db.commit()
    await db.refresh(user)
    return UserRead.model_validate(user)


@router.get("/me/sessions", response_model=list[SessionRead])
async def list_my_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SessionRead]:
    sessions = SessionRepository(db)
    rows = await sessions.list_for_user(current_user.id)
    return [SessionRead.model_validate(s, from_attributes=True) for s in rows]
