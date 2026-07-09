from dataclasses import dataclass
from time import monotonic


@dataclass
class RateLimitDecision:
    allowed: bool
    remaining: int
    reset_seconds: int


class InMemoryRateLimiter:
    def __init__(self, limit: int = 30, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._buckets: dict[str, list[float]] = {}

    def check(self, key: str) -> RateLimitDecision:
        now = monotonic()
        bucket = [stamp for stamp in self._buckets.get(key, []) if now - stamp < self.window_seconds]
        allowed = len(bucket) < self.limit
        if allowed:
            bucket.append(now)
        self._buckets[key] = bucket
        remaining = max(self.limit - len(bucket), 0)
        oldest = min(bucket) if bucket else now
        reset = max(int(self.window_seconds - (now - oldest)), 0)
        return RateLimitDecision(allowed=allowed, remaining=remaining, reset_seconds=reset)
