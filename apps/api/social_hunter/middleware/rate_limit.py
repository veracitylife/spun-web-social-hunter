"""Rate limiting middleware for FastAPI."""
from fastapi import HTTPException, Request, status

from social_hunter.services.rate_limit import RateLimitService


class RateLimitMiddleware:
    """Middleware to enforce rate limits on search endpoints."""

    def __init__(self, rate_limit_service: RateLimitService):
        self.rate_limit_service = rate_limit_service

    async def check_rate_limit(
        self,
        request: Request,
        user_id: str,
        plan_id: str,
        target_hash: str,
    ) -> None:
        """Check rate limit and raise HTTPException if exceeded."""
        ip_address = request.client.host if request.client else "unknown"
        allowed, reason = await self.rate_limit_service.check_rate_limit(
            user_id=user_id,
            plan_id=plan_id,
            ip_address=ip_address,
            target_hash=target_hash,
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=reason,
            )
