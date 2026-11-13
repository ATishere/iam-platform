"""Audit helper: redact sensitive keys recursively, then persist.

Append-only ở app layer — module này chỉ có `log()`, không có update/delete.
"""

import re
from typing import Any

_SENSITIVE_KEYS = {
    "password",
    "new_password",
    "old_password",
    "password_hash",
    "token",
    "refresh_token",
    "access_token",
    "authorization",
    "secret",
    "api_key",
    "reset_token",
}
_REDACTED = "[REDACTED]"


def _redact_value(key: str, value: Any) -> Any:
    if key.lower() in _SENSITIVE_KEYS and value is not None:
        return _REDACTED
    return value


def redact(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: _redact_value(k, redact(v)) for k, v in data.items()}
    if isinstance(data, list):
        return [redact(v) for v in data]
    if isinstance(data, str):
        # Redact Bearer tokens trong log message
        return re.sub(r"Bearer\s+[A-Za-z0-9_\-\.]+", "Bearer [REDACTED]", data)
    return data
