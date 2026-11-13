"""Argon2id password hashing.

Params lấy từ Settings (time_cost=3, memory_cost=64MiB, parallelism=4 — spec mục 2).
Chuỗi hash trả về là format chuẩn Argon2 `$argon2id$v=19$m=...,t=...,p=...$salt$hash`,
bao gồm mọi tham số cần để verify.
"""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

from app.core.config import get_settings


def _hasher() -> PasswordHasher:
    s = get_settings()
    return PasswordHasher(
        time_cost=s.argon2_time_cost,
        memory_cost=s.argon2_memory_cost,
        parallelism=s.argon2_parallelism,
        hash_len=s.argon2_hash_len,
        salt_len=s.argon2_salt_len,
    )


def hash_password(password: str) -> str:
    return _hasher().hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        _hasher().verify(password_hash, password)
        return True
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    try:
        return _hasher().check_needs_rehash(password_hash)
    except InvalidHashError:
        return True
