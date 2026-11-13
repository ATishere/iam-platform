"""Sliding-window rate limiter dùng Redis sorted set (D32–D35).

Mỗi hit là một member unique `{now_ms}:{nonce}`. Lua script chạy atomic:
xoá entry cũ hơn window → thêm entry mới → đếm → set TTL.

Fail-open: Redis lỗi/không có → cho request đi qua và log warning.
Identity (IP/email) được hash SHA-256 trước khi đưa vào key để không lưu
thông tin nhạy cảm dạng plaintext trong Redis.
"""

import hashlib
import logging
import time
import uuid

from app.core.config import get_settings
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

_SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local now_ms = tonumber(ARGV[1])
local window_ms = tonumber(ARGV[2])
local member = ARGV[3]

redis.call('ZREMRANGEBYSCORE', key, 0, now_ms - window_ms)
redis.call('ZADD', key, now_ms, member)
local count = redis.call('ZCARD', key)
redis.call('PEXPIRE', key, window_ms + 1000)

local retry_ms = 0
if count > 0 then
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    retry_ms = tonumber(oldest[2]) + window_ms - now_ms
    if retry_ms < 0 then retry_ms = 0 end
end
return {count, retry_ms}
"""


def _identity_hash(identity: str) -> str:
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:32]


def build_key(scope: str, identity: str) -> str:
    settings = get_settings()
    return f"{settings.ratelimit_key_prefix}:{scope}:{_identity_hash(identity)}"


async def check_rate_limit(
    *,
    scope: str,
    identity: str,
    limit: int,
    window_seconds: int,
) -> tuple[bool, int]:
    """Trả (allowed, retry_after_seconds). Fail-open khi Redis down."""
    client = get_redis()
    if client is None:
        logger.warning("rate limit skip (redis not initialized) scope=%s", scope)
        return True, 0

    now_ms = int(time.time() * 1000)
    window_ms = window_seconds * 1000
    member = f"{now_ms}:{uuid.uuid4().hex}"

    try:
        count, retry_ms = await client.eval(
            _SLIDING_WINDOW_LUA,
            1,
            build_key(scope, identity),
            now_ms,
            window_ms,
            member,
        )
    except Exception:  # noqa: BLE001
        logger.warning("rate limit fail-open scope=%s", scope, exc_info=True)
        return True, 0

    if int(count) > limit:
        retry_after = max(1, (int(retry_ms) + 999) // 1000)
        return False, retry_after
    return True, 0
