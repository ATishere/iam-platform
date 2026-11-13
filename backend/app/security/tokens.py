"""Token utilities:
- Access token: JWT HS256, TTL 15 phút, claims sub/sid/org/jti/iat/exp/type.
- Refresh token: opaque, `secrets.token_urlsafe(48)`, DB lưu sha256 hex.
- Password reset token: opaque, `secrets.token_urlsafe(32)`, DB lưu sha256 hex.

KHÔNG đặt permission vào access token (xem D11).
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from jose import JWTError, jwt

from app.core.config import get_settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


# --- Access token ---

def create_access_token(
    *, user_id: UUID, session_id: UUID, organization_id: UUID
) -> str:
    s = get_settings()
    now = _now()
    payload = {
        "sub": str(user_id),
        "sid": str(session_id),
        "org": str(organization_id),
        "jti": str(uuid4()),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=s.access_token_expire_minutes)).timestamp()),
    }
    return jwt.encode(payload, s.secret_key, algorithm=s.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Raise JWTError nếu invalid/expired. Caller phải catch."""
    s = get_settings()
    payload = jwt.decode(token, s.secret_key, algorithms=[s.jwt_algorithm])
    if payload.get("type") != "access":
        raise JWTError("wrong token type")
    return payload


# --- Opaque tokens ---

def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def generate_password_reset_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(raw: str) -> str:
    """SHA256 hex — deterministic, đủ để chống lộ DB."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
