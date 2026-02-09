import json
import hashlib
from typing import Any, Optional

from app.core.redis_client import redis_client


def make_key(prefix: str, *parts: str) -> str:
    raw = prefix + ":" + ":".join(parts)
    # hash to keep keys short/safe
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]
    return f"cache:{prefix}:{digest}"


async def cache_get(key: str) -> Optional[Any]:
    val = await redis_client.get(key)
    if not val:
        return None
    return json.loads(val)


async def cache_set(key: str, value: Any, ttl_seconds: int) -> None:
    await redis_client.setex(key, ttl_seconds, json.dumps(value, default=str))


async def cache_delete_prefix(prefix: str) -> None:
    """
    Simple namespace invalidation. Uses SCAN so it won’t block Redis.
    """
    pattern = f"cache:{prefix}:*"
    async for k in redis_client.scan_iter(match=pattern, count=200):
        await redis_client.delete(k)
