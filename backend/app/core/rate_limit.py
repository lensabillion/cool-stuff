import time
from fastapi import HTTPException, Request, status
from app.core.redis_client import redis_client


def get_client_ip(request: Request) -> str:
    """
    Works on local and on GCP VM. If later you add a reverse proxy, it can pass x-forwarded-for.
    """
    xf = request.headers.get("x-forwarded-for")
    if xf:
        return xf.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


async def rate_limit(*, key: str, limit: int, window_seconds: int) -> None:
    """
    Fixed-window limiter: allow N requests per window_seconds.
    Stores counter in Redis with TTL so it auto-cleans.
    """
    now = int(time.time())
    window = now // window_seconds
    redis_key = f"rl:{key}:{window}"

    count = await redis_client.incr(redis_key)
    if count == 1:
        await redis_client.expire(redis_key, window_seconds)

    if count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded ({limit}/{window_seconds}s)",
        )


async def rate_limit_ip(request: Request, *, action: str, limit: int, window_seconds: int) -> None:
    ip = get_client_ip(request)
    await rate_limit(key=f"{action}:ip:{ip}", limit=limit, window_seconds=window_seconds)


async def rate_limit_user(current_user: dict, *, action: str, limit: int, window_seconds: int) -> None:
    user_id = current_user.get("id") or "unknown"
    await rate_limit(key=f"{action}:user:{user_id}", limit=limit, window_seconds=window_seconds)


async def rate_limit_ip_and_user(
    request: Request,
    current_user: dict,
    *,
    action: str,
    ip_limit: int,
    user_limit: int,
    window_seconds: int,
) -> None:
    await rate_limit_ip(request, action=action, limit=ip_limit, window_seconds=window_seconds)
    await rate_limit_user(current_user, action=action, limit=user_limit, window_seconds=window_seconds)
