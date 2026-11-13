"""Rate limit dependencies (D32, D40, D41).

Dùng FastAPI dependency thay vì middleware: route khai báo tường minh,
429 trả về cùng format lỗi API, và test có thể bật/tắt qua settings.

Account-level login limit (theo email) chưa làm được ở dependency vì
body chưa được parse — xem tech debt D33.
"""

import logging
from collections.abc import Awaitable, Callable

from fastapi import HTTPException, Request, status

from app.api.deps import client_ip
from app.core.config import get_settings
from app.security.ratelimit import check_rate_limit

logger = logging.getLogger(__name__)

_Dep = Callable[..., Awaitable[None]]


def _make_dep(scope: str, limit_attr: str, window_attr: str) -> _Dep:
    async def _dep(request: Request) -> None:
        settings = get_settings()
        if not settings.ratelimit_enabled:
            return
        limit = int(getattr(settings, limit_attr))
        window = int(getattr(settings, window_attr))
        ip = client_ip(request) or "unknown"
        allowed, retry_after = await check_rate_limit(
            scope=scope, identity=ip, limit=limit, window_seconds=window
        )
        if not allowed:
            logger.warning(
                "security.ratelimit_exceeded scope=%s ip=%s path=%s",
                scope,
                ip,
                request.url.path,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests",
                headers={"Retry-After": str(retry_after)},
            )

    return _dep


rate_limit_login_ip = _make_dep(
    "login:ip", "ratelimit_login_ip_limit", "ratelimit_login_ip_window"
)
rate_limit_register_ip = _make_dep(
    "register:ip", "ratelimit_register_ip_limit", "ratelimit_register_ip_window"
)
rate_limit_refresh_ip = _make_dep(
    "refresh:ip", "ratelimit_refresh_ip_limit", "ratelimit_refresh_ip_window"
)
rate_limit_forgot_ip = _make_dep(
    "forgot:ip", "ratelimit_forgot_ip_limit", "ratelimit_forgot_ip_window"
)
