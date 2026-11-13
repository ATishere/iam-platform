"""Auth orchestration.

Mỗi method public chạy trong 1 transaction. Caller (FastAPI route) commit
sau khi method trả về thành công. Nếu service raise HTTPException, route
sẽ rollback — nhưng để an toàn, service tự rollback trước khi raise khi
cần (vd: audit failure cho login fail, sau đó mới raise).
"""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.session import Session
from app.models.user import User
from app.repositories.audit_repo import AuditRepository
from app.repositories.password_reset_repo import PasswordResetRepository
from app.repositories.refresh_token_repo import RefreshTokenRepository
from app.repositories.session_repo import SessionRepository
from app.repositories.user_repo import UserRepository
from app.security import tokens
from app.security.password import hash_password, verify_password

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


_DUMMY_HASH = hash_password("dummy-password-for-timing-mitigation")


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.sessions = SessionRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)
        self.reset_tokens = PasswordResetRepository(db)
        self.audit = AuditRepository(db)
        self.settings = get_settings()

    # ---------- Register ----------

    async def register(
        self,
        *,
        organization_id: UUID,
        email: str,
        password: str,
        full_name: str | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> User:
        existing = await self.users.get_by_email(organization_id, email)
        if existing is not None:
            # Không tiết lộ email tồn tại hay không → trả 400 generic.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to register with provided credentials",
            )
        user = User(
            organization_id=organization_id,
            email=email.lower(),
            full_name=full_name,
            password_hash=hash_password(password),
        )
        await self.users.create(user)
        await self.audit.insert(
            organization_id=organization_id,
            actor_id=user.id,
            action="register.success",
            resource_type="user",
            resource_id=str(user.id),
            ip_address=ip_address,
            user_agent=user_agent,
            outcome="success",
            metadata={"email": email},
        )
        return user

    # ---------- Login ----------

    async def login(
        self,
        *,
        organization_id: UUID,
        email: str,
        password: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> tuple[User, Session, str, str]:
        """Trả (user, session, access_token, refresh_token_raw)."""
        user = await self.users.get_by_email(organization_id, email)

        if user is None:
            await self._audit_login_failure(
                organization_id, None, email, ip_address, user_agent, "user_not_found"
            )
            # Vẫn hash dummy để timing không lộ user tồn tại
            verify_password(password, _DUMMY_HASH)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        # Locked?
        now = _now()
        if user.locked_until is not None and user.locked_until > now:
            await self._audit_login_failure(
                organization_id, user.id, email, ip_address, user_agent, "account_locked"
            )
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked",
            )
        # Auto-unlock nếu hết hạn lock
        if user.locked_until is not None and user.locked_until <= now:
            user.is_locked = False
            user.locked_until = None
            user.failed_login_attempts = 0

        if not user.is_active:
            await self._audit_login_failure(
                organization_id, user.id, email, ip_address, user_agent, "inactive"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive"
            )

        if not verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= self.settings.max_failed_login_attempts:
                user.locked_until = now + timedelta(
                    minutes=self.settings.lockout_duration_minutes
                )
                user.is_locked = True
                await self.audit.insert(
                    organization_id=organization_id,
                    actor_id=user.id,
                    action="login.locked",
                    resource_type="user",
                    resource_id=str(user.id),
                    ip_address=ip_address,
                    user_agent=user_agent,
                    outcome="failure",
                    metadata={"email": email},
                )
            await self._audit_login_failure(
                organization_id, user.id, email, ip_address, user_agent, "bad_password"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        # Success
        user.failed_login_attempts = 0
        user.is_locked = False
        user.locked_until = None
        user.last_login_at = now

        session = Session(
            user_id=user.id,
            organization_id=organization_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.sessions.create(session)

        # D31.1: generate family_id trước khi tạo RefreshToken (tránh bug assign sau id)
        family_id = uuid4()
        refresh_raw = tokens.generate_refresh_token()
        family_id = uuid4()
        refresh = RefreshToken(
            user_id=user.id,
            session_id=session.id,
            organization_id=organization_id,
            family_id=family_id,
            token_hash=tokens.hash_token(refresh_raw),
            expires_at=now + timedelta(days=self.settings.refresh_token_expire_days),
        )
        await self.refresh_tokens.create(refresh)

        access = tokens.create_access_token(
            user_id=user.id,
            session_id=session.id,
            organization_id=organization_id,
        )

        await self.audit.insert(
            organization_id=organization_id,
            actor_id=user.id,
            action="login.success",
            resource_type="session",
            resource_id=str(session.id),
            ip_address=ip_address,
            user_agent=user_agent,
            outcome="success",
            metadata={"email": email},
        )
        return user, session, access, refresh_raw

    # ---------- Refresh ----------

    async def refresh(
        self,
        *,
        refresh_token_raw: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> tuple[str, str]:
        token_hash = tokens.hash_token(refresh_token_raw)
        row = await self.refresh_tokens.get_by_hash_for_update(token_hash)

        if row is None:
            # Không xác định được organization → không insert audit DB (FK),
            # chỉ ghi stdlib log. Phase 4 sẽ có system-event sink.
            logger.warning("refresh.invalid: token not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        # Reuse detected — token đã revoke hoặc đã dùng
        if row.revoked_at is not None or row.used_at is not None:
            await self.refresh_tokens.revoke_family(row.family_id)
            await self.sessions.revoke(row.session_id)
            await self.audit.insert(
                organization_id=row.organization_id,
                actor_id=row.user_id,
                action="refresh.reuse_detected",
                resource_type="refresh_token",
                resource_id=str(row.id),
                ip_address=ip_address,
                user_agent=user_agent,
                outcome="failure",
                metadata={"family_id": str(row.family_id)},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        if row.expires_at <= _now():
            await self.audit.insert(
                organization_id=row.organization_id,
                actor_id=row.user_id,
                action="refresh.expired",
                resource_type="refresh_token",
                resource_id=str(row.id),
                ip_address=ip_address,
                user_agent=user_agent,
                outcome="failure",
                metadata={},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        session = await self.sessions.get_active(row.session_id)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        # Rotate
        new_raw = tokens.generate_refresh_token()
        new_token = RefreshToken(
            user_id=row.user_id,
            session_id=row.session_id,
            organization_id=row.organization_id,
            family_id=row.family_id,
            parent_id=row.id,
            token_hash=tokens.hash_token(new_raw),
            expires_at=_now()
            + timedelta(days=self.settings.refresh_token_expire_days),
        )
        await self.refresh_tokens.create(new_token)
        await self.refresh_tokens.mark_used_and_replace(row.id, new_token.id)
        await self.sessions.touch(session.id)

        access = tokens.create_access_token(
            user_id=row.user_id,
            session_id=session.id,
            organization_id=row.organization_id,
        )
        await self.audit.insert(
            organization_id=row.organization_id,
            actor_id=row.user_id,
            action="refresh.success",
            resource_type="refresh_token",
            resource_id=str(new_token.id),
            ip_address=ip_address,
            user_agent=user_agent,
            outcome="success",
            metadata={"family_id": str(row.family_id)},
        )
        return access, new_raw

    # ---------- Logout ----------

    async def logout(
        self,
        *,
        refresh_token_raw: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        token_hash = tokens.hash_token(refresh_token_raw)
        row = await self.refresh_tokens.get_by_hash_for_update(token_hash)
        if row is None:
            # Idempotent: không lộ token có tồn tại hay không
            return
        await self.refresh_tokens.revoke_all_for_session(row.session_id)
        await self.sessions.revoke(row.session_id)
        await self.audit.insert(
            organization_id=row.organization_id,
            actor_id=row.user_id,
            action="logout",
            resource_type="session",
            resource_id=str(row.session_id),
            ip_address=ip_address,
            user_agent=user_agent,
            outcome="success",
            metadata={},
        )

    # ---------- Logout all ----------

    async def logout_all(
        self,
        *,
        user: User,
        ip_address: str | None,
        user_agent: str | None,
    ) -> int:
        """Revoke toàn bộ session + refresh token của user."""
        await self.sessions.revoke_all_for_user(user.id)
        count = await self.refresh_tokens.revoke_all_for_user(user.id)
        await self.audit.insert(
            organization_id=user.organization_id,
            actor_id=user.id,
            action="auth.logout_all",
            resource_type="user",
            resource_id=str(user.id),
            ip_address=ip_address,
            user_agent=user_agent,
            outcome="success",
            metadata={"revoked_tokens": count},
        )
        return count

    # ---------- Change password ----------

    async def change_password(
        self,
        *,
        user_id: UUID,
        old_password: str,
        new_password: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        user = await self.users.get_by_id_for_update(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
            )
        if not verify_password(old_password, user.password_hash):
            await self.audit.insert(
                organization_id=user.organization_id,
                actor_id=user.id,
                action="password.change.failure",
                resource_type="user",
                resource_id=str(user.id),
                ip_address=ip_address,
                user_agent=user_agent,
                outcome="failure",
                metadata={"reason": "bad_old_password"},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Old password is incorrect",
            )
        user.password_hash = hash_password(new_password)
        # Revoke mọi session cũ + refresh token
        await self.sessions.revoke_all_for_user(user.id)
        await self.refresh_tokens.revoke_all_for_user(user.id)
        await self.audit.insert(
            organization_id=user.organization_id,
            actor_id=user.id,
            action="password.change.success",
            resource_type="user",
            resource_id=str(user.id),
            ip_address=ip_address,
            user_agent=user_agent,
            outcome="success",
            metadata={},
        )

    # ---------- Forgot / reset password ----------

    async def forgot_password(
        self,
        *,
        organization_id: UUID,
        email: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> str | None:
        """Luôn trả 202 ở route; method trả raw token nếu user tồn tại (để test)."""
        user = await self.users.get_by_email(organization_id, email)
        if user is None or not user.is_active:
            return None
        raw = tokens.generate_password_reset_token()
        await self.reset_tokens.create(
            PasswordResetToken(
                user_id=user.id,
                token_hash=tokens.hash_token(raw),
                expires_at=_now()
                + timedelta(minutes=self.settings.password_reset_token_expire_minutes),
            )
        )
        await self.audit.insert(
            organization_id=organization_id,
            actor_id=user.id,
            action="password.reset.requested",
            resource_type="user",
            resource_id=str(user.id),
            ip_address=ip_address,
            user_agent=user_agent,
            outcome="success",
            metadata={},
        )
        return raw

    async def reset_password(
        self,
        *,
        reset_token_raw: str,
        new_password: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        token_hash = tokens.hash_token(reset_token_raw)
        row = await self.reset_tokens.get_by_hash_for_update(token_hash)
        if row is None:
            # Không xác định được organization → không insert audit DB (FK).
            logger.warning("password.reset.invalid: token not found")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        user = await self.users.get_by_id_for_update(row.user_id)
        if row.used_at is not None or row.expires_at <= _now() or user is None:
            if user is not None:
                await self.audit.insert(
                    organization_id=user.organization_id,
                    actor_id=user.id,
                    action="password.reset.invalid",
                    resource_type="password_reset_token",
                    resource_id=str(row.id),
                    ip_address=ip_address,
                    user_agent=user_agent,
                    outcome="failure",
                    metadata={},
                )
            else:
                logger.warning(
                    "password.reset.invalid: user not found for token %s", row.id
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        user.password_hash = hash_password(new_password)
        await self.reset_tokens.mark_used(row.id)
        await self.reset_tokens.invalidate_all_for_user(user.id)
        await self.sessions.revoke_all_for_user(user.id)
        await self.refresh_tokens.revoke_all_for_user(user.id)
        await self.audit.insert(
            organization_id=user.organization_id,
            actor_id=user.id,
            action="password.reset.success",
            resource_type="user",
            resource_id=str(user.id),
            ip_address=ip_address,
            user_agent=user_agent,
            outcome="success",
            metadata={},
        )

    # ---------- helpers ----------

    async def _audit_login_failure(
        self,
        organization_id: UUID,
        actor_id: UUID | None,
        email: str,
        ip_address: str | None,
        user_agent: str | None,
        reason: str,
    ) -> None:
        await self.audit.insert(
            organization_id=organization_id,
            actor_id=actor_id,
            action="login.failure",
            resource_type="user",
            resource_id=str(actor_id) if actor_id else None,
            ip_address=ip_address,
            user_agent=user_agent,
            outcome="failure",
            metadata={"email": email, "reason": reason},
        )
