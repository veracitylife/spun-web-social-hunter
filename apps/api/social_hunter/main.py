import csv
import io
import json
from datetime import datetime, timezone
from uuid import UUID

from dataclasses import asdict

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from social_hunter import __version__
from social_hunter.config import get_settings
from social_hunter.connectors.registry import run_connectors
from social_hunter.models import (
    ApiKeyReference,
    ApiKeyTestRequest,
    DeploymentHardeningStatus,
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
    PayPalSettings,
    PlanResponse,
    ProviderConfig,
    ProviderRuntimeTestRequest,
    ProviderRuntimeTestResponse,
    ProxyConnectionTestRequest,
    ProxyConnectionTestResponse,
    ProxyImportRequest,
    ProxyRouteRule,
    ProxySettings,
    ProxyTestResponse,
    SearchJob,
    SearchRequest,
    SearchResponse,
    SignupRequest,
    SourceCapability,
    SourceGate,
    SourceHealth,
    TenantAccount,
    UserAccountView,
    MailSettings,
    WhatsMyNameImportRequest,
    WhatsMyNameImportResponse,
)
from social_hunter.services.billing import PAYPAL_EMAIL, PLANS, paypal_checkout_url
from social_hunter.services.jobs import create_job, get_job, list_jobs
from social_hunter.services.provider_catalog import default_api_key_references, default_proxy_route_rules, provider_catalog
from social_hunter.services.provider_runtime import test_provider_runtime
from social_hunter.services.proxy_tester import test_proxy_connections
from social_hunter.services.reports import render_markdown_report
from social_hunter.services.security import UserAccount, default_users, hash_password, login_user, require_admin, require_session, serialize_user
from social_hunter.services.state import PersistentState, dump_model
from social_hunter.services.source_health import get_source_health
from social_hunter.services.whatsmyname import fetch_whatsmyname, local_whatsmyname_status
from social_hunter.sources import SOURCE_CAPABILITIES, engine_contract

settings = get_settings()
state = PersistentState()


def _load_list(key: str, default: list, model):
    return [model(**item) for item in state.get(key, [dump_model(entry) for entry in default])]


def _save_state(key: str, value) -> None:
    state.set(key, dump_model(value))


def _append_audit(event: dict[str, str]) -> None:
    audit_events.append({"timestamp": datetime.now(timezone.utc).isoformat(), **event})
    _save_state("audit_events", audit_events[-500:])


general_settings = GeneralSettings(**state.get("general_settings", GeneralSettings().model_dump(mode="json")))
api_key_references: list[ApiKeyReference] = _load_list("api_key_references", default_api_key_references(), ApiKeyReference)
source_gates: list[SourceGate] = _load_list(
    "source_gates",
    [
        SourceGate(
            source_id=source.id,
            enabled=source.status in {"ready", "stubbed"},
            requires_approval=source.status == "needs_api_key",
            note=source.terms_note,
        )
        for source in SOURCE_CAPABILITIES
    ],
    SourceGate,
)
proxy_settings = ProxySettings(**state.get("proxy_settings", ProxySettings().model_dump(mode="json")))
proxy_route_rules: list[ProxyRouteRule] = _load_list("proxy_route_rules", default_proxy_route_rules(), ProxyRouteRule)
contact_submissions: list[ContactSubmissionRecord] = _load_list("contact_submissions", [], ContactSubmissionRecord)
audit_events: list[dict[str, str]] = state.get("audit_events", [])
tenants: list[TenantAccount] = _load_list(
    "tenants",
    [
        TenantAccount(id="platform", name="Platform", plan="operator", monthly_search_limit=100000),
        TenantAccount(id="demo-tenant", name="Demo Tenant", plan="growth"),
    ],
    TenantAccount,
)
user_accounts: list[UserAccount] = [UserAccount(**item) for item in state.get("user_accounts", [asdict(user) for user in default_users()])]
mail_settings = MailSettings(**state.get("mail_settings", MailSettings().model_dump(mode="json")))
paypal_settings = PayPalSettings(**state.get("paypal_settings", PayPalSettings().model_dump(mode="json")))
hardening_status = DeploymentHardeningStatus(**state.get("hardening_status", DeploymentHardeningStatus().model_dump(mode="json")))

app = FastAPI(
    title="Social Hunter API",
    version=__version__,
    description="Educational OSINT aggregation API scaffold.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["*"],
)


@app.post("/api/auth/member/login", response_model=AuthResponse)
async def member_login(request: LoginRequest) -> AuthResponse:
    session = login_user(user_accounts, request.username, request.password, required_role="member")
    _save_state("user_accounts", [asdict(user) for user in user_accounts])
    _append_audit({"actor": session.username, "action": "member_login", "status": "ok", "tenant_id": session.tenant_id})
    return AuthResponse(ok=True, role="member", display_name=session.username, token=session.token, message="Member session issued.")


@app.post("/api/auth/member/password-reset")
async def member_password_reset(request: PasswordResetRequest) -> dict[str, str]:
    _append_audit({"actor": request.email, "action": "password_reset_requested", "status": "queued"})
    return {"status": "queued", "message": "Password reset email flow is queued for mail-provider wiring."}


@app.post("/api/auth/member/signup")
async def member_signup(request: SignupRequest) -> dict[str, str]:
    record = ContactSubmissionRecord(name=request.name, email=request.email, company=request.company, message=f"Signup request for {request.plan} plan")
    contact_submissions.append(record)
    if not any(user.email.lower() == request.email.lower() for user in user_accounts):
        user_accounts.append(UserAccount(username=request.email, email=request.email, role="member", tenant_id="demo-tenant", plan=request.plan, password_hash=hash_password("change-me-after-activation"), active=False))
    _save_state("contact_submissions", contact_submissions)
    _save_state("user_accounts", [asdict(user) for user in user_accounts])
    _append_audit({"actor": request.email, "action": "member_signup_requested", "plan": request.plan})
    return {"status": "received", "message": "Signup request received. Activate account after payment confirmation."}


@app.post("/api/auth/admin/login", response_model=AuthResponse)
async def admin_login(request: LoginRequest) -> AuthResponse:
    session = login_user(user_accounts, request.username, request.password, required_role="admin")
    _save_state("user_accounts", [asdict(user) for user in user_accounts])
    _append_audit({"actor": session.username, "action": "admin_login", "status": "ok", "tenant_id": session.tenant_id})
    return AuthResponse(ok=True, role="admin", display_name=session.username, token=session.token, message="Admin session issued.")

@app.post("/api/auth/admin/password-reset")
async def admin_password_reset(request: PasswordResetRequest) -> dict[str, str]:
    _append_audit({"actor": request.email, "action": "admin_password_reset_requested", "status": "queued"})
    return {"status": "queued", "message": "Admin password reset email flow is queued for mail-provider wiring."}


@app.post("/api/contact", response_model=ContactSubmissionRecord)
async def submit_contact(request: ContactSubmission) -> ContactSubmissionRecord:
    record = ContactSubmissionRecord(**request.model_dump())
    contact_submissions.append(record)
    _append_audit({"actor": request.email, "action": "contact_submission", "status": "new"})
    return record


@app.get("/api/admin/contact-submissions", response_model=list[ContactSubmissionRecord])
async def admin_contact_submissions(_admin = Depends(require_admin)) -> list[ContactSubmissionRecord]:
    return contact_submissions



@app.get("/api/admin/provider-configs", response_model=list[ProviderConfig])
async def admin_provider_configs(_admin = Depends(require_admin)) -> list[ProviderConfig]:
    return provider_catalog()


@app.get("/api/admin/settings/source-gates", response_model=list[SourceGate])
async def get_source_gates(_admin = Depends(require_admin)) -> list[SourceGate]:
    return source_gates


@app.put("/api/admin/settings/source-gates", response_model=list[SourceGate])
async def update_source_gates(request: list[SourceGate], _admin = Depends(require_admin)) -> list[SourceGate]:
    global source_gates
    source_gates = request
    _save_state("source_gates", source_gates)
    _append_audit({"actor": "admin", "action": "source_gates_updated", "status": "saved"})
    return source_gates

@app.get("/api/admin/settings/general", response_model=GeneralSettings)
async def get_general_settings(_admin = Depends(require_admin)) -> GeneralSettings:
    return general_settings


@app.put("/api/admin/settings/general", response_model=GeneralSettings)
async def update_general_settings(request: GeneralSettings, _admin = Depends(require_admin)) -> GeneralSettings:
    global general_settings
    general_settings = request
    _save_state("general_settings", general_settings)
    _append_audit({"actor": "admin", "action": "general_settings_updated", "status": "saved"})
    return general_settings


@app.get("/api/admin/settings/api-keys", response_model=list[ApiKeyReference])
async def get_api_key_references(_admin = Depends(require_admin)) -> list[ApiKeyReference]:
    return api_key_references


@app.put("/api/admin/settings/api-keys", response_model=list[ApiKeyReference])
async def update_api_key_references(request: list[ApiKeyReference], _admin = Depends(require_admin)) -> list[ApiKeyReference]:
    global api_key_references
    api_key_references = request
    _save_state("api_key_references", api_key_references)
    _append_audit({"actor": "admin", "action": "api_key_references_updated", "status": "saved"})
    return api_key_references


@app.post("/api/admin/settings/api-keys/test")
async def test_api_key_reference(request: ApiKeyTestRequest, _admin = Depends(require_admin)) -> dict[str, str | bool]:
    catalog_by_id = {provider.id: provider for provider in provider_catalog()}
    provider = catalog_by_id.get(request.provider_id)
    ref = request.vault_reference.strip()
    no_secret_required = request.credential_type == "none"
    ok = no_secret_required or (ref.startswith("VAULT_REF_") and ref != "VAULT_REF_PROVIDER_KEY")
    connector_function = provider.connector_function if provider else "unmapped"
    message = (
        "No API credential required; connector function is mapped."
        if no_secret_required
        else "Vault reference accepted; live provider calls require Vault runtime secret resolution."
        if ok
        else "Use a Vault reference such as VAULT_REF_PROVIDER_KEY. Do not paste raw API keys."
    )
    _append_audit({"actor": "admin", "action": "api_key_reference_tested", "provider": request.provider, "status": "ok" if ok else "needs_vault_ref"})
    return {"ok": ok, "provider": request.provider, "provider_id": request.provider_id, "connector_function": connector_function, "message": message}


@app.get("/api/admin/settings/proxies", response_model=ProxySettings)
async def get_proxy_settings(_admin = Depends(require_admin)) -> ProxySettings:
    return proxy_settings


@app.put("/api/admin/settings/proxies", response_model=ProxySettings)
async def update_proxy_settings(request: ProxySettings, _admin = Depends(require_admin)) -> ProxySettings:
    global proxy_settings
    proxy_settings = request
    _save_state("proxy_settings", proxy_settings)
    _append_audit({"actor": "admin", "action": "proxy_settings_updated", "status": "saved"})
    return proxy_settings


@app.post("/api/admin/settings/proxies/import", response_model=ProxySettings)
async def import_proxy_settings(request: ProxyImportRequest, _admin = Depends(require_admin)) -> ProxySettings:
    global proxy_settings
    entries = [line.strip() for line in request.entries_text.splitlines() if line.strip() and not line.strip().startswith("#")]
    proxy_settings.manual_entries = entries
    _save_state("proxy_settings", proxy_settings)
    _append_audit({"actor": "admin", "action": "proxy_entries_imported", "status": "saved", "count": str(len(entries))})
    return proxy_settings


@app.get("/api/admin/settings/proxies/routes", response_model=list[ProxyRouteRule])
async def get_proxy_route_rules(_admin = Depends(require_admin)) -> list[ProxyRouteRule]:
    return proxy_route_rules


@app.put("/api/admin/settings/proxies/routes", response_model=list[ProxyRouteRule])
async def update_proxy_route_rules(request: list[ProxyRouteRule], _admin = Depends(require_admin)) -> list[ProxyRouteRule]:
    global proxy_route_rules
    proxy_route_rules = request
    _save_state("proxy_route_rules", proxy_route_rules)
    _append_audit({"actor": "admin", "action": "proxy_route_rules_updated", "status": "saved"})
    return proxy_route_rules


@app.post("/api/admin/settings/proxies/test", response_model=ProxyTestResponse)
async def test_proxy_settings(request: ProxySettings, _admin = Depends(require_admin)) -> ProxyTestResponse:
    invalid_entries = [entry for entry in request.manual_entries if len(entry.split(":")) < 2]
    valid = len(request.manual_entries) - len(invalid_entries)
    return ProxyTestResponse(
        ok=len(invalid_entries) == 0,
        tested=len(request.manual_entries),
        valid_format=valid,
        invalid_entries=invalid_entries,
        message="Format validation complete. Use proxies only for allowlisted provider API egress; bypass/evasion use is not supported.",
    )


@app.post("/api/admin/settings/proxies/connection-test", response_model=ProxyConnectionTestResponse)
async def test_proxy_connections_endpoint(request: ProxyConnectionTestRequest, _admin = Depends(require_admin)) -> ProxyConnectionTestResponse:
    result = await test_proxy_connections(request.entries, request.target_url, request.timeout_seconds, request.concurrency)
    _append_audit({"actor": "admin", "action": "proxy_connection_tested", "status": "ok" if result.ok else "review", "tested": str(result.tested), "connected": str(result.connected)})
    return result



@app.get("/api/admin/users", response_model=list[UserAccountView])
async def admin_users(_admin = Depends(require_admin)) -> list[UserAccountView]:
    return [UserAccountView(**serialize_user(user)) for user in user_accounts]


@app.get("/api/admin/tenants", response_model=list[TenantAccount])
async def admin_tenants(_admin = Depends(require_admin)) -> list[TenantAccount]:
    return tenants


@app.put("/api/admin/tenants", response_model=list[TenantAccount])
async def update_admin_tenants(request: list[TenantAccount], _admin = Depends(require_admin)) -> list[TenantAccount]:
    global tenants
    tenants = request
    _save_state("tenants", tenants)
    _append_audit({"actor": "admin", "action": "tenants_updated", "status": "saved"})
    return tenants


@app.get("/api/admin/settings/mail", response_model=MailSettings)
async def get_mail_settings(_admin = Depends(require_admin)) -> MailSettings:
    return mail_settings


@app.put("/api/admin/settings/mail", response_model=MailSettings)
async def update_mail_settings(request: MailSettings, _admin = Depends(require_admin)) -> MailSettings:
    global mail_settings
    mail_settings = request
    _save_state("mail_settings", mail_settings)
    _append_audit({"actor": "admin", "action": "mail_settings_updated", "status": "saved"})
    return mail_settings


@app.get("/api/admin/settings/paypal", response_model=PayPalSettings)
async def get_paypal_settings(_admin = Depends(require_admin)) -> PayPalSettings:
    return paypal_settings


@app.put("/api/admin/settings/paypal", response_model=PayPalSettings)
async def update_paypal_settings(request: PayPalSettings, _admin = Depends(require_admin)) -> PayPalSettings:
    global paypal_settings
    paypal_settings = request
    _save_state("paypal_settings", paypal_settings)
    _append_audit({"actor": "admin", "action": "paypal_settings_updated", "status": "saved"})
    return paypal_settings


@app.get("/api/admin/hardening", response_model=DeploymentHardeningStatus)
async def get_hardening_status(_admin = Depends(require_admin)) -> DeploymentHardeningStatus:
    return hardening_status


@app.get("/api/admin/whatsmyname/status")
async def whatsmyname_status(_admin = Depends(require_admin)) -> dict[str, object]:
    return local_whatsmyname_status()


@app.post("/api/admin/whatsmyname/import", response_model=WhatsMyNameImportResponse)
async def import_whatsmyname(request: WhatsMyNameImportRequest, _admin = Depends(require_admin)) -> WhatsMyNameImportResponse:
    result = await fetch_whatsmyname(limit=request.limit, dry_run=request.dry_run)
    _append_audit({"actor": "admin", "action": "whatsmyname_import", "status": "dry_run" if request.dry_run else "saved", "importable": str(result.get("importable", 0))})
    return WhatsMyNameImportResponse(**result)


@app.post("/api/admin/provider-runtime/test", response_model=ProviderRuntimeTestResponse)
async def provider_runtime_test(request: ProviderRuntimeTestRequest, _admin = Depends(require_admin)) -> ProviderRuntimeTestResponse:
    result = await test_provider_runtime(request.provider_id, request.sample_target)
    _append_audit({"actor": "admin", "action": "provider_runtime_test", "provider_id": request.provider_id, "status": result.status})
    return result

@app.get("/api/admin/audit")
async def admin_audit(_admin = Depends(require_admin)) -> list[dict[str, str]]:
    return audit_events[-100:]


@app.post("/api/billing/paypal/checkout", response_model=PayPalCheckoutResponse)
async def paypal_checkout(request: PayPalCheckoutRequest) -> PayPalCheckoutResponse:
    plan_id = request.plan.lower()
    plan = next((item for item in paypal_settings.plans if item.id.lower() == plan_id and item.enabled), None)
    if plan is None:
        raise HTTPException(status_code=400, detail="invalid plan")
    checkout_url = paypal_checkout_url(
        plan.id,
        receiver_email=paypal_settings.receiver_email,
        amount=plan.amount,
        currency=plan.currency or paypal_settings.currency,
        item_name=plan.paypal_item_name or f"Social Hunter {plan.name} Plan",
    )
    return PayPalCheckoutResponse(plan=plan.id, paypal_email=paypal_settings.receiver_email, checkout_url=checkout_url, message="Redirect user to PayPal and activate after verified payment confirmation.")


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
    return [PlanResponse(**plan.model_dump()) for plan in sorted(paypal_settings.plans, key=lambda item: item.sort_order) if plan.enabled and plan.public]


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
