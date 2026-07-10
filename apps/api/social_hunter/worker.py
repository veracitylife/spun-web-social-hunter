"""Production worker for Social Hunter."""
import asyncio
import json
import logging
import signal
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from social_hunter.connectors.registry import run_connectors
from social_hunter.db import DATABASE_URL
from social_hunter.models import Finding, SearchJob, SearchRequest, SearchResponse
from social_hunter.repositories.search_repository import SearchRepository
from social_hunter.services.queue import JobQueue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Worker:
    """Redis-backed async worker for processing OSINT jobs."""

    def __init__(self):
        self.queue = JobQueue()
        self.running = False
        self.engine = create_async_engine(DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
        self.async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

    @asynccontextmanager
    async def get_db(self):
        """Get database session."""
        async with self.async_session() as session:
            yield session

    async def process_job(self, job_data: dict) -> None:
        """Process a single job."""
        job_id = UUID(job_data["id"])
        payload = job_data["payload"]

        logger.info(f"Processing job {job_id}")

        async with self.get_db() as session:
            repo = SearchRepository(session)

            try:
                # Reconstruct request
                request = SearchRequest(**payload["request"])

                # Update status to running
                await repo.update_search_status(job_id, "running")

                # Run connectors
                findings = await run_connectors(request)

                # Build response
                response = SearchResponse(
                    target_type=request.target_type,
                    target=request.target,
                    status="completed",
                    findings=findings,
                    next_actions=[
                        "Review source attribution before classroom discussion.",
                        "Export JSON/CSV/Markdown for assignment artifacts.",
                    ],
                )

                # Save findings
                await repo.save_findings(job_id, findings)

                # Mark complete
                await repo.update_search_status(job_id, "completed")

                # Complete in queue
                await self.queue.complete(str(job_id))

                logger.info(f"Job {job_id} completed with {len(findings)} findings")

            except Exception as exc:
                logger.exception(f"Job {job_id} failed")
                await repo.update_search_status(
                    job_id,
                    "failed",
                    error_message=str(exc),
                )
                await self.queue.fail(str(job_id), str(exc))

    async def run(self) -> None:
        """Main worker loop."""
        self.running = True
        logger.info("Worker started")

        while self.running:
            try:
                job = await self.queue.dequeue(timeout=5)
                if job:
                    await self.process_job(job)
                else:
                    # No jobs, brief pause
                    await asyncio.sleep(0.1)
            except Exception as exc:
                logger.exception("Worker error")
                await asyncio.sleep(1)

    async def shutdown(self) -> None:
        """Graceful shutdown."""
        logger.info("Worker shutting down...")
        self.running = False


async def main():
    """Entry point."""
    worker = Worker()

    # Handle signals
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(worker.shutdown()))

    try:
        await worker.run()
    finally:
        await worker.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
