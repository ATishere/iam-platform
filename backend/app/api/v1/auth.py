from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    client_ip,
    client_user_agent,
    get_current_user,
    get_default_organization,
)
from app.api.deps_ratelimit import (
    rate_limit_forgot_ip,
    rate_limit_login_ip,
    rate_limit_refresh_ip,
    rate_limit_register_ip,
)
from app.core.config import get_settings
from app.db.session import get_db
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenPair,
)
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_register_ip)],
)
async def register(
    body: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_default_organization),
) -> UserRead:
    svc = AuthService(db)
    user = await svc.register(
        organization_id=org.id,
        email=body.email,
        password=body.password,
        full_name=body.full_name,
        ip_address=client_ip(request),
        user_agent=client_user_agent(request),
    )
    await db.commit()
    return UserRead.model_validate(user)


@router.post(
    "/login",
    response_model=TokenPair,
    dependencies=[Depends(rate_limit_login_ip)],
)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_default_organization),
) -> TokenPair:
    settings = get_settings()
    svc = AuthService(db)
    try:
        _user, _session, access, refresh = await svc.login(
            organization_id=org.id,
            email=body.email,
            password=body.password,
            ip_address=client_ip(request),
            user_agent=client_user_agent(request),
        )
        await db.commit()
    except HTTPException:
        # Audit failure đã insert trước khi raise → commit để lưu lại
        await db.commit()
        raise
    return TokenPair(
        access_token=access,
        refresh_token=refresh,
        access_expires_in=settings.access_token_expire_minutes * 60,
        refresh_expires_in=settings.refresh_token_expire_days * 86400,
    )


@router.post(
    "/refresh",
    response_model=TokenPair,
    dependencies=[Depends(rate_limit_refresh_ip)],
)
async def refresh(
    body: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    settings = get_settings()
    svc = AuthService(db)
    try:
        access, refresh_raw = await svc.refresh(
            refresh_token_raw=body.refresh_token,
            ip_address=client_ip(request),
            user_agent=client_user_agent(request),
        )
        await db.commit()
    except HTTPException:
        await db.commit()
        raise
    return TokenPair(
        access_token=access,
        refresh_token=refresh_raw,
        access_expires_in=settings.access_token_expire_minutes * 60,
        refresh_expires_in=settings.refresh_token_expire_days * 86400,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: LogoutRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> None:
    svc = AuthService(db)
    try:
        await svc.logout(
            refresh_token_raw=body.refresh_token,
            ip_address=client_ip(request),
            user_agent=client_user_agent(request),
        )
        await db.commit()
    except HTTPException:
        await db.commit()
        raise


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: ChangePasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    svc = AuthService(db)
    try:
        await svc.change_password(
            user_id=current_user.id,
            old_password=body.old_password,
            new_password=body.new_password,
            ip_address=client_ip(request),
            user_agent=client_user_agent(request),
        )
        await db.commit()
    except HTTPException:
        await db.commit()
        raise


@router.post(
    "/forgot-password",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(rate_limit_forgot_ip)],
)
async def forgot_password(
    body: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_default_organization),
) -> dict[str, str]:
    settings = get_settings()
    svc = AuthService(db)
    raw = await svc.forgot_password(
        organization_id=org.id,
        email=body.email,
        ip_address=client_ip(request),
        user_agent=client_user_agent(request),
    )
    await db.commit()
    if raw is not None:
        if settings.app_env == "production":
            # D31.2: guard log reset token — fail loud thay vì silent ở production
            raise RuntimeError(
                "Password reset email service not implemented "
                "(Phase 2 stub). Cannot serve forgot-password in production."
            )
        import logging

        logging.getLogger(__name__).warning(
            "password reset token generated (NOT SENT — no email service in Phase 2). "
            "user_email=%s token=%s",
            body.email,
            raw,
        )
    # Luôn 202 để chống enumeration
    return {"message": "If the email exists, a reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    body: ResetPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> None:
    svc = AuthService(db)
    try:
        await svc.reset_password(
            reset_token_raw=body.token,
            new_password=body.new_password,
            ip_address=client_ip(request),
            user_agent=client_user_agent(request),
        )
        await db.commit()
    except HTTPException:
        await db.commit()
        raise


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    svc = AuthService(db)
    await svc.logout_all(
        user=current_user,
        ip_address=client_ip(request),
        user_agent=client_user_agent(request),
    )
    await db.commit()