import csv
import io
import json
from uuid import UUID

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from social_hunter import __version__
from social_hunter.config import get_settings
from social_hunter.connectors.registry import run_connectors
from social_hunter.models import (
    EngineHandoffContract,
    ExportRequest,
    ExportResponse,
    HealthResponse,
    LaunchChecklistItem,
    PlanResponse,
    SearchJob,
    SearchRequest,
    SearchResponse,
    SourceCapability,
    SourceHealth,
)
from social_hunter.services.billing import PLANS
from social_hunter.services.jobs import create_job, get_job, list_jobs
from social_hunter.services.reports import render_markdown_report
from social_hunter.services.source_health import get_source_health
from social_hunter.sources import SOURCE_CAPABILITIES, engine_contract

settings = get_settings()

app = FastAPI(
    title="Social Hunter API",
    version=__version__,
    description="Educational OSINT aggregation API scaffold.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="social-hunter-api", version=__version__)


@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    if not request.consent_confirmed:
        raise HTTPException(status_code=400, detail="consent_confirmed is required for searches")

    findings = await run_connectors(request)
    return SearchResponse(
        target_type=request.target_type,
        target=request.target,
        findings=findings,
        next_actions=[
            "Verify high-confidence findings manually before operational use.",
            "Export only reports tied to an authenticated user account.",
            "Add provider API keys through Vault before enabling paid sources.",
        ],
    )


@app.post("/api/search/jobs", response_model=SearchJob)
async def enqueue_search(request: SearchRequest) -> SearchJob:
    if not request.consent_confirmed:
        raise HTTPException(status_code=400, detail="consent_confirmed is required for searches")
    return await create_job(request)


@app.get("/api/search/jobs", response_model=list[SearchJob])
async def search_jobs() -> list[SearchJob]:
    return list_jobs()


@app.get("/api/search/jobs/{job_id}", response_model=SearchJob)
async def search_job(job_id: UUID) -> SearchJob:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.get("/api/sources", response_model=list[SourceCapability])
async def sources() -> list[SourceCapability]:
    return SOURCE_CAPABILITIES


@app.get("/api/sources/health", response_model=list[SourceHealth])
async def source_health() -> list[SourceHealth]:
    return get_source_health()


@app.get("/api/plans", response_model=list[PlanResponse])
async def plans() -> list[PlanResponse]:
    return [PlanResponse(**plan.__dict__) for plan in PLANS]


@app.get("/api/admin/launch-checklist", response_model=list[LaunchChecklistItem])
async def launch_checklist() -> list[LaunchChecklistItem]:
    return [
        LaunchChecklistItem(id="ui", label="Dashboard UI", status="done", owner="product", note="Search, reports, sources, and admin views are implemented."),
        LaunchChecklistItem(id="api", label="Core API", status="done", owner="backend", note="Search, jobs, exports, sources, plans, and contract endpoints are implemented."),
        LaunchChecklistItem(id="db", label="Database persistence", status="partial", owner="backend", note="Models exist; migrations and repository wiring remain."),
        LaunchChecklistItem(id="auth", label="Authentication", status="partial", owner="platform", note="Demo auth context exists; production auth provider remains."),
        LaunchChecklistItem(id="providers", label="Paid provider wiring", status="partial", owner="integrations", note="Client skeletons exist; Vault-backed runtime keys remain."),
        LaunchChecklistItem(id="billing", label="Billing", status="partial", owner="growth", note="Plan model exists; Stripe checkout and webhooks remain."),
        LaunchChecklistItem(id="legal", label="Legal docs", status="partial", owner="ops", note="Templates exist; legal review remains before public launch."),
    ]


@app.get("/api/engine-contract", response_model=EngineHandoffContract)
async def get_engine_contract() -> EngineHandoffContract:
    return engine_contract()


@app.post("/api/export", response_model=ExportResponse)
async def export_report(request: ExportRequest) -> ExportResponse:
    if request.format == "json":
        return ExportResponse(
            filename=f"social-hunter-{request.search.id}.json",
            content_type="application/json",
            content=json.dumps(request.search.model_dump(mode="json"), indent=2),
        )

    if request.format == "markdown":
        return ExportResponse(
            filename=f"social-hunter-{request.search.id}.md",
            content_type="text/markdown",
            content=render_markdown_report(request.search),
        )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["source", "category", "status", "confidence", "title", "url", "evidence", "checked_at"])
    for finding in request.search.findings:
        writer.writerow([
            finding.source,
            finding.category,
            finding.status,
            finding.confidence,
            finding.title,
            str(finding.url) if finding.url else "",
            finding.evidence,
            finding.checked_at.isoformat(),
        ])

    return ExportResponse(
        filename=f"social-hunter-{request.search.id}.csv",
        content_type="text/csv",
        content=output.getvalue(),
    )
