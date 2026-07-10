from datetime import datetime, timezone
from uuid import UUID

from social_hunter.connectors.registry import run_connectors
from social_hunter.models import SearchJob, SearchRequest, SearchResponse

_JOBS: dict[UUID, SearchJob] = {}


async def create_job(request: SearchRequest) -> SearchJob:
    job = SearchJob(request=request)
    _JOBS[job.id] = job
    await run_job(job.id)
    return _JOBS[job.id]


async def run_job(job_id: UUID) -> SearchJob:
    job = _JOBS[job_id]
    job.status = "running"
    job.updated_at = datetime.now(timezone.utc)
    try:
        findings = await run_connectors(job.request)
        job.result = SearchResponse(
            target_type=job.request.target_type,
            target=job.request.target,
            findings=findings,
            next_actions=[
                "Review source attribution before classroom discussion.",
                "Export JSON/CSV/Markdown for assignment artifacts.",
            ],
        )
        job.status = "completed"
    except Exception as exc:  # pragma: no cover - defensive scaffold
        job.status = "failed"
        job.error = f"{exc.__class__.__name__}: {exc}"
    job.updated_at = datetime.now(timezone.utc)
    _JOBS[job.id] = job
    return job


def get_job(job_id: UUID) -> SearchJob | None:
    return _JOBS.get(job_id)


def list_jobs() -> list[SearchJob]:
    return sorted(_JOBS.values(), key=lambda job: job.created_at, reverse=True)
