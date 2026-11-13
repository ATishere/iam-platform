"""Async Redis client singleton (Phase 4).

Fail-open: rate limiting không được phép làm sập auth flow. Nếu Redis
không khả dụng, `get_redis()` trả None và caller bỏ qua check.
"""

import logging

import redis.asyncio as aioredis

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_client: aioredis.Redis | None = None


async def init_redis() -> None:
    global _client
    settings = get_settings()
    _client = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=1,
    )
    try:
        await _client.ping()
        logger.info("redis connected: %s", settings.redis_url)
    except Exception:  # noqa: BLE001
        # Giữ client để retry lazy; rate limit fail-open sẽ tự log warning.
        logger.warning("redis unavailable at startup: %s", settings.redis_url)


async def close_redis() -> None:
    global _client
    if _client is not None:
        try:
            await _client.aclose()
        except Exception:  # noqa: BLE001
            logger.warning("error closing redis client", exc_info=True)
        _client = None


def get_redis() -> aioredis.Redis | None:
    return _client
