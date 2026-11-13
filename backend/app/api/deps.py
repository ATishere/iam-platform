"""FastAPI dependencies: DB session, current user từ access token, org resolution."""

import logging
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.organization import Organization
from app.models.user import User
from app.repositories.session_repo import SessionRepository
from app.repositories.user_repo import UserRepository
from app.security.tokens import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)

logger = logging.getLogger(__name__)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        logger.warning(
            "security.invalid_jwt ip=%s path=%s reason=decode_failed",
            client_ip(request),
            request.url.path,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = UUID(payload["sub"])
        session_id = UUID(payload["sid"])
    except (KeyError, ValueError):
        logger.warning(
            "security.invalid_jwt ip=%s path=%s reason=invalid_payload",
            client_ip(request),
            request.url.path,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )

    # Session phải active (revoke → token chết ngay, không đợi hết hạn)
    sessions = SessionRepository(db)
    session = await sessions.get_active(session_id)
    if session is None or session.user_id != user_id:
        logger.warning(
            "security.session_inactive ip=%s path=%s reason=session_revoked",
            client_ip(request),
            request.url.path,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session is not active"
        )

    users = UserRepository(db)
    user = await users.get_by_id(user_id)
    if user is None or not user.is_active:
        logger.warning(
            "security.session_inactive ip=%s path=%s reason=user_inactive",
            client_ip(request),
            request.url.path,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not active"
        )

    # Gắn để route dùng lại
    request.state.user = user
    request.state.session_id = session_id
    return user


async def get_current_session_id(request: Request) -> UUID:
    return request.state.session_id


async def get_default_organization(
    db: AsyncSession = Depends(get_db),
) -> Organization:
    """MVP single-org: lấy org đầu tiên. Phase 3 sẽ thay bằng org theo user."""
    stmt = select(Organization).order_by(Organization.created_at.asc()).limit(1)
    org = (await db.execute(stmt)).scalar_one_or_none()
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No organization configured. Run seed script.",
        )
    return org


def client_ip(request: Request) -> str | None:
    # Không tin X-Forwarded-For trừ khi có reverse proxy tin cậy cấu hình.
    # MVP: dùng request.client.
    return request.client.host if request.client else None


def client_user_agent(request: Request) -> str | None:
    ua = request.headers.get("user-agent")
    return ua[:512] if ua else None
