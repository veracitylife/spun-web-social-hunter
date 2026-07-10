"""Redis-backed job queue for Social Hunter."""
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import redis.asyncio as redis


class JobQueue:
    """Redis-backed job queue with priority support."""

    def __init__(self, redis_url: str = "redis://redis:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.queue_key = "socialhunter:queue"
        self.processing_key = "socialhunter:processing"
        self.dead_letter_key = "socialhunter:failed"

    async def enqueue(
        self,
        job_id: UUID,
        job_type: str,
        payload: dict[str, Any],
        priority: int = 5,
    ) -> None:
        """Add job to queue with priority (1-10, lower = higher priority)."""
        job_data = {
            "id": str(job_id),
            "type": job_type,
            "payload": payload,
            "priority": priority,
            "enqueued_at": datetime.now(timezone.utc).isoformat(),
            "attempt": 1,
        }
        # Use sorted set for priority queue
        score = priority * 1000000000 + int(datetime.now(timezone.utc).timestamp())
        await self.redis.zadd(self.queue_key, {json.dumps(job_data): score})

    async def dequeue(self, timeout: int = 5) -> dict[str, Any] | None:
        """Get next job from queue."""
        # Get highest priority job (lowest score)
        result = await self.redis.bzpopmin(self.queue_key, timeout=timeout)
        if not result:
            return None

        _, job_json, _ = result
        job = json.loads(job_json)

        # Track in processing set
        job["started_at"] = datetime.now(timezone.utc).isoformat()
        await self.redis.hset(
            self.processing_key,
            job["id"],
            json.dumps(job),
        )

        return job

    async def complete(self, job_id: str) -> None:
        """Mark job as completed."""
        await self.redis.hdel(self.processing_key, job_id)

    async def fail(
        self,
        job_id: str,
        error: str,
        max_retries: int = 3,
    ) -> None:
        """Handle job failure with retry logic."""
        job_data = await self.redis.hget(self.processing_key, job_id)
        if not job_data:
            return

        job = json.loads(job_data)
        await self.redis.hdel(self.processing_key, job_id)

        if job.get("attempt", 1) < max_retries:
            # Re-queue with higher priority (lower number)
            job["attempt"] = job.get("attempt", 1) + 1
            job["last_error"] = error
            score = (job.get("priority", 5) - 1) * 1000000000
            await self.redis.zadd(self.queue_key, {json.dumps(job): score})
        else:
            # Move to dead letter queue
            job["failed_at"] = datetime.now(timezone.utc).isoformat()
            job["error"] = error
            await self.redis.lpush(self.dead_letter_key, json.dumps(job))

    async def get_queue_stats(self) -> dict[str, int]:
        """Get queue statistics."""
        queued = await self.redis.zcard(self.queue_key)
        processing = await self.redis.hlen(self.processing_key)
        failed = await self.redis.llen(self.dead_letter_key)
        return {
            "queued": queued,
            "processing": processing,
            "failed": failed,
        }
