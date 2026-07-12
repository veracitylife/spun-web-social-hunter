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
    ApiKeyReference,
    ApiKeyTestRequest,
    AuthResponse,
    ContactSubmission,
    ContactSubmissionRecord,
    EngineHandoffContract,
    ExportRequest,
    ExportResponse,
    GeneralSettings,
    HealthResponse,
    LaunchChecklistItem,
    LoginRequest,
    PasswordResetRequest,
    PayPalCheckoutRequest,
    PayPalCheckoutResponse,
    PlanResponse,
    ProxySettings,
    ProxyTestResponse,
    SearchJob,
    SearchRequest,
    SearchResponse,
    SignupRequest,
    SourceCapability,
    SourceHealth,
)
from social_hunter.services.billing import PAYPAL_EMAIL, PLANS, paypal_checkout_url
from social_hunter.services.jobs import create_job, get_job, list_jobs
from social_hunter.services.reports import render_markdown_report
from social_hunter.services.source_health import get_source_health
from social_hunter.sources import SOURCE_CAPABILITIES, engine_contract

settings = get_settings()

general_settings = GeneralSettings()
api_key_references: list[ApiKeyReference] = [
    ApiKeyReference(provider="Hunter.io"),
    ApiKeyReference(provider="People Data Labs"),
    ApiKeyReference(provider="Have I Been Pwned"),
    ApiKeyReference(provider="Twilio Lookup"),
    ApiKeyReference(provider="Brave Search"),
    ApiKeyReference(provider="Google Places"),
]
proxy_settings = ProxySettings()
contact_submissions: list[ContactSubmissionRecord] = []
audit_events: list[dict[str, str]] = []

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


@app.post("/api/auth/member/login", response_model=AuthResponse)
async def member_login(request: LoginRequest) -> AuthResponse:
    audit_events.append({"actor": request.username, "action": "member_login", "status": "demo_ok"})
    return AuthResponse(ok=True, role="member", display_name=request.username, token="demo-member-session", message="Demo member session issued. Replace with production auth before launch.")


@app.post("/api/auth/member/password-reset")
async def member_password_reset(request: PasswordResetRequest) -> dict[str, str]:
    audit_events.append({"actor": request.email, "action": "password_reset_requested", "status": "queued"})
    return {"status": "queued", "message": "Password reset email flow is queued for mail-provider wiring."}


@app.post("/api/auth/member/signup")
async def member_signup(request: SignupRequest) -> dict[str, str]:
    contact_submissions.append(ContactSubmissionRecord(name=request.name, email=request.email, company=request.company, message=f"Signup request for {request.plan} plan"))
    audit_events.append({"actor": request.email, "action": "member_signup_requested", "plan": request.plan})
    return {"status": "received", "message": "Signup request received. Activate account after payment confirmation."}


@app.post("/api/auth/admin/login", response_model=AuthResponse)
async def admin_login(request: LoginRequest) -> AuthResponse:
    audit_events.append({"actor": request.username, "action": "admin_login", "status": "demo_ok"})
    return AuthResponse(ok=True, role="admin", display_name=request.username, token="demo-admin-session", message="Demo admin session issued. Replace with production auth before launch.")


@app.post("/api/contact", response_model=ContactSubmissionRecord)
async def submit_contact(request: ContactSubmission) -> ContactSubmissionRecord:
    record = ContactSubmissionRecord(**request.model_dump())
    contact_submissions.append(record)
    audit_events.append({"actor": request.email, "action": "contact_submission", "status": "new"})
    return record


@app.get("/api/admin/contact-submissions", response_model=list[ContactSubmissionRecord])
async def admin_contact_submissions() -> list[ContactSubmissionRecord]:
    return contact_submissions


@app.get("/api/admin/settings/general", response_model=GeneralSettings)
async def get_general_settings() -> GeneralSettings:
    return general_settings


@app.put("/api/admin/settings/general", response_model=GeneralSettings)
async def update_general_settings(request: GeneralSettings) -> GeneralSettings:
    global general_settings
    general_settings = request
    audit_events.append({"actor": "admin", "action": "general_settings_updated", "status": "saved"})
    return general_settings


@app.get("/api/admin/settings/api-keys", response_model=list[ApiKeyReference])
async def get_api_key_references() -> list[ApiKeyReference]:
    return api_key_references


@app.put("/api/admin/settings/api-keys", response_model=list[ApiKeyReference])
async def update_api_key_references(request: list[ApiKeyReference]) -> list[ApiKeyReference]:
    global api_key_references
    api_key_references = request
    audit_events.append({"actor": "admin", "action": "api_key_references_updated", "status": "saved"})
    return api_key_references


@app.post("/api/admin/settings/api-keys/test")
async def test_api_key_reference(request: ApiKeyTestRequest) -> dict[str, str | bool]:
    ok = request.vault_reference.startswith("VAULT_REF_") or request.vault_reference == ""
    return {"ok": ok, "provider": request.provider, "message": "Vault reference accepted for configuration. Live provider test requires Vault runtime integration."}


@app.get("/api/admin/settings/proxies", response_model=ProxySettings)
async def get_proxy_settings() -> ProxySettings:
    return proxy_settings


@app.put("/api/admin/settings/proxies", response_model=ProxySettings)
async def update_proxy_settings(request: ProxySettings) -> ProxySettings:
    global proxy_settings
    proxy_settings = request
    audit_events.append({"actor": "admin", "action": "proxy_settings_updated", "status": "saved"})
    return proxy_settings


@app.post("/api/admin/settings/proxies/test", response_model=ProxyTestResponse)
async def test_proxy_settings(request: ProxySettings) -> ProxyTestResponse:
    valid = sum(1 for entry in request.manual_entries if len(entry.split(":")) >= 2)
    return ProxyTestResponse(ok=valid == len(request.manual_entries), tested=len(request.manual_entries), valid_format=valid, message="Format validation complete. Network proxy testing should run only for approved provider egress.")


@app.get("/api/admin/audit")
async def admin_audit() -> list[dict[str, str]]:
    return audit_events[-100:]


@app.post("/api/billing/paypal/checkout", response_model=PayPalCheckoutResponse)
async def paypal_checkout(request: PayPalCheckoutRequest) -> PayPalCheckoutResponse:
    plan_id = request.plan.lower()
    if plan_id not in PLANS:
        raise HTTPException(status_code=400, detail="invalid plan")
    return PayPalCheckoutResponse(plan=plan_id, paypal_email=PAYPAL_EMAIL, checkout_url=paypal_checkout_url(plan_id), message="Redirect user to PayPal and activate after verified payment confirmation.")


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
    if isinstance(PLANS, dict):
        return [
            PlanResponse(
                id=plan_id,
                name=str(plan["name"]),
                monthly_search_limit=int(plan["monthly_searches"]),
                export_enabled=bool(plan["exports"]),
                api_access_enabled=bool(plan["api_access"]),
            )
            for plan_id, plan in PLANS.items()
        ]
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
