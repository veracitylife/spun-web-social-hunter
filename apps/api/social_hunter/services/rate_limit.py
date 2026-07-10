"""Rate limiting service for per-user, per-IP, and per-target-type enforcement."""
import hashlib
import time
from typing import Optional

from pydantic import BaseModel, Field


class RateLimitConfig(BaseModel):
    """Rate limit configuration."""
    # Per-user limits
    searches_per_minute_free: int = 5
    searches_per_hour_free: int = 100
    searches_per_day_free: int = 500
    searches_per_minute_professional: int = 20
    searches_per_hour_professional: int = 500
    searches_per_day_professional: int = 5000
    searches_per_minute_enterprise: int = 100
    searches_per_hour_enterprise: int = 5000
    searches_per_day_enterprise: int = 50000

    # Per-IP limits (anonymous/fallback)
    searches_per_minute_anonymous: int = 2
    searches_per_hour_anonymous: int = 20

    # Per-target limits
    same_target_cooldown_seconds: int = 30  # Prevent rapid re-searches of same target


class RateLimitBucket(BaseModel):
    """In-memory rate limit bucket (demo; production uses Redis)."""
    key: str
    count_minute: int = 0
    count_hour: int = 0
    count_day: int = 0
    last_reset_minute: float = 0
    last_reset_hour: float = 0
    last_reset_day: float = 0
    last_target_search: dict[str, float] = Field(default_factory=dict)  # target_hash -> timestamp


class RateLimitService:
    """Enforces rate limits across user, IP, and target dimensions."""

    def __init__(self, config: RateLimitConfig, redis_client=None):
        self.config = config
        self.redis_client = redis_client
        self.buckets: dict[str, RateLimitBucket] = {}  # key -> bucket (demo only)

    def get_plan_limits(self, plan_id: str) -> tuple[int, int, int]:
        """Return (per_minute, per_hour, per_day) limits for a plan."""
        plan_id = plan_id.lower()
        if plan_id == "enterprise":
            return (
                self.config.searches_per_minute_enterprise,
                self.config.searches_per_hour_enterprise,
                self.config.searches_per_day_enterprise,
            )
        elif plan_id == "professional":
            return (
                self.config.searches_per_minute_professional,
                self.config.searches_per_hour_professional,
                self.config.searches_per_day_professional,
            )
        else:  # free or default
            return (
                self.config.searches_per_minute_free,
                self.config.searches_per_hour_free,
                self.config.searches_per_day_free,
            )

    async def check_rate_limit(
        self,
        user_id: str,
        plan_id: str,
        ip_address: str,
        target_hash: str,
    ) -> tuple[bool, Optional[str]]:
        """
        Check rate limits for user + IP + target.
        Returns (allowed: bool, reason: Optional[str])
        """
        now = time.time()
        user_key = f"ratelimit:user:{user_id}"
        ip_key = f"ratelimit:ip:{ip_address}"
        target_key = f"ratelimit:target:{target_hash}"

        # Check per-user limits
        per_min, per_hour, per_day = self.get_plan_limits(plan_id)
        user_bucket = await self._get_or_create_bucket(user_key)
        if not await self._increment_bucket(user_bucket, per_min, per_hour, per_day, now):
            return False, f"User rate limit exceeded (plan: {plan_id})"

        # Check per-IP limits (for anonymous/fallback)
        if not user_id.startswith("demo-") and not user_id.startswith("system-"):
            ip_bucket = await self._get_or_create_bucket(ip_key)
            if not await self._increment_bucket(
                ip_bucket,
                self.config.searches_per_minute_anonymous,
                self.config.searches_per_hour_anonymous,
                0,  # No daily limit per IP
                now,
            ):
                return False, "IP rate limit exceeded"

        # Check target cooldown (prevent rapid re-searches)
        target_bucket = await self._get_or_create_bucket(target_key)
        if target_hash in target_bucket.last_target_search:
            time_since_last = now - target_bucket.last_target_search[target_hash]
            if time_since_last < self.config.same_target_cooldown_seconds:
                return False, f"Please wait {int(self.config.same_target_cooldown_seconds - time_since_last)}s before re-searching this target"
        target_bucket.last_target_search[target_hash] = now

        return True, None

    async def _get_or_create_bucket(self, key: str) -> RateLimitBucket:
        """Retrieve or create a rate limit bucket (demo; production uses Redis)."""
        if key not in self.buckets:
            self.buckets[key] = RateLimitBucket(key=key)
        return self.buckets[key]

    async def _increment_bucket(self, bucket: RateLimitBucket, per_min: int, per_hour: int, per_day: int, now: float) -> bool:
        """Increment bucket counters and check limits. Returns True if under limits."""
        # Reset counters if windows have passed
        if now - bucket.last_reset_minute > 60:
            bucket.count_minute = 0
            bucket.last_reset_minute = now
        if now - bucket.last_reset_hour > 3600:
            bucket.count_hour = 0
            bucket.last_reset_hour = now
        if now - bucket.last_reset_day > 86400:
            bucket.count_day = 0
            bucket.last_reset_day = now

        # Check limits
        if bucket.count_minute >= per_min:
            return False
        if bucket.count_hour >= per_hour:
            return False
        if per_day > 0 and bucket.count_day >= per_day:
            return False

        # Increment
        bucket.count_minute += 1
        bucket.count_hour += 1
        bucket.count_day += 1
        return True

    def hash_target(self, target: str) -> str:
        """Hash a target for rate limit tracking (no reversible PII)."""
        return hashlib.sha256(target.lower().encode()).hexdigest()[:16]
