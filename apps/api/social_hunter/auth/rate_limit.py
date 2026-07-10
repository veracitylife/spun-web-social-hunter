"""Rate limiting for Social Hunter."""
from datetime import datetime, timedelta, timezone
from typing import Annotated

import redis.asyncio as redis
from fastapi import Depends, HTTPException, Request, status

from social_hunter.auth.middleware import AuthContext, get_auth_context


class RateLimiter:
    """Redis-backed rate limiter."""

    def __init__(self, redis_url: str = "redis://redis:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=True)

    async def is_allowed(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int, int]:
        """Check if request is allowed under rate limit."""
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=window_seconds)

        # Remove old entries
        await self.redis.zremrangebyscore(key, 0, window_start.timestamp())

        # Count current requests
        current_count = await self.redis.zcard(key)

        if current_count >= limit:
            # Get oldest entry for retry-after
            oldest = await self.redis.zrange(key, 0, 0, withscores=True)
            retry_after = int(oldest[0][1] + window_seconds - now.timestamp()) if oldest else window_seconds
            return False, current_count, retry_after

        # Add current request
        await self.redis.zadd(key, {str(now.timestamp()): now.timestamp()})
        await self.redis.expire(key, window_seconds)

        return True, current_count + 1, 0


rate_limiter = RateLimiter()


async def rate_limit_by_user(
    request: Request,
    context: Annotated[AuthContext, Depends(get_auth_context)],
) -> None:
    """Rate limit by user ID."""
    key = f"rate_limit:user:{context.user_id}"
    allowed, current, retry_after = await rate_limiter.is_allowed(key, 60, 60)  # 60/min

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Retry after {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )


async def rate_limit_by_ip(
    request: Request,
) -> None:
    """Rate limit by IP address."""
    client_ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:ip:{client_ip}"
    allowed, current, retry_after = await rate_limiter.is_allowed(key, 30, 60)  # 30/min

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for anonymous users",
        )
