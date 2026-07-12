from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl


class TargetType(str, Enum):
    username = "username"
    email = "email"
    domain = "domain"
    ip = "ip"
    phone = "phone"


class FindingStatus(str, Enum):
    found = "found"
    not_found = "not_found"
    unknown = "unknown"
    skipped = "skipped"
    error = "error"


class ComplianceFlag(str, Enum):
    public_source = "public_source"
    api_terms_required = "api_terms_required"
    no_raw_secret = "no_raw_secret"
    no_bypass = "no_bypass"
    user_authorized = "user_authorized"


class SearchRequest(BaseModel):
    target_type: TargetType
    target: str = Field(min_length=2, max_length=255)
    consent_confirmed: bool = False
    source_groups: list[str] = Field(default_factory=lambda: [
        "username_profile",
        "email_intel",
        "phone_intel",
        "person_enrichment",
        "business_contact",
        "domain_intel",
        "web_search",
        "breach",
        "ip",
    ])
    dry_run: bool = True


class Finding(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    source: str
    category: str
    status: FindingStatus
    confidence: float = Field(ge=0, le=1)
    title: str
    url: HttpUrl | None = None
    evidence: str
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    compliance_flags: list[ComplianceFlag] = Field(default_factory=list)


class SearchResponse(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    target_type: TargetType
    target: str
    status: Literal["completed", "queued", "failed"] = "completed"
    findings: list[Finding]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    next_actions: list[str] = Field(default_factory=list)


class SearchJob(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    request: SearchRequest
    status: Literal["queued", "running", "completed", "failed"] = "queued"
    result: SearchResponse | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SourceCapability(BaseModel):
    id: str
    name: str
    category: str
    target_types: list[TargetType]
    status: Literal["ready", "stubbed", "needs_api_key", "disabled"]
    terms_note: str
    data_returned: list[str]
    raw_payload_storage_allowed: bool = False


class SourceHealth(BaseModel):
    source_id: str
    status: Literal["healthy", "degraded", "disabled", "needs_key"]
    latency_ms: float | None = None
    last_checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    note: str


class ExportRequest(BaseModel):
    search: SearchResponse
    format: Literal["json", "csv", "markdown"] = "json"


class ExportResponse(BaseModel):
    filename: str
    content_type: str
    content: str


class AuditEvent(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    actor: str = "demo-analyst"
    action: str
    target_type: TargetType | None = None
    target_hash: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EngineHandoffContract(BaseModel):
    version: str = "0.1"
    accepted_input: dict[str, str]
    expected_output_fields: list[str]
    prohibited_capabilities: list[str]
    integration_notes: list[str]


class BillingPlan(BaseModel):
    id: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=80)
    amount: float = Field(default=49, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    interval: Literal["month", "year", "one_time"] = "month"
    monthly_search_limit: int = Field(default=250, ge=0)
    export_enabled: bool = True
    api_access_enabled: bool = False
    description: str = Field(default="", max_length=500)
    services: list[str] = Field(default_factory=list)
    enabled: bool = True
    public: bool = True
    paypal_item_name: str = Field(default="", max_length=120)
    sort_order: int = 0


class PlanResponse(BillingPlan):
    pass


class LaunchChecklistItem(BaseModel):
    id: str
    label: str
    status: Literal["done", "partial", "blocked", "todo"]
    owner: str
    note: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str


class LoginRequest(BaseModel):
    username: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=1, max_length=255)


class AuthResponse(BaseModel):
    ok: bool
    role: Literal["member", "admin"]
    display_name: str
    token: str
    message: str


class PasswordResetRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)


class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    company: str = Field(default="", max_length=255)
    plan: str = Field(default="growth", max_length=50)


class ContactSubmission(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    company: str = Field(default="", max_length=255)
    message: str = Field(min_length=3, max_length=2000)


class ContactSubmissionRecord(ContactSubmission):
    id: UUID = Field(default_factory=uuid4)
    status: Literal["new", "reviewed", "replied"] = "new"
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GeneralSettings(BaseModel):
    application_name: str = "Social Hunter"
    public_url: str = "https://social-hunter.spunwebtechnology.com/"
    support_email: str = "techpronow@gmail.com"
    default_plan: str = "growth"
    require_consent: bool = True
    normalized_evidence_only: bool = True
    high_cost_provider_approval: bool = True
    export_retention_days: int = 90


class ApiKeyReference(BaseModel):
    provider: str
    provider_id: str = ""
    source_id: str = ""
    credential_type: str = "api_key"
    connector_function: str = ""
    vault_reference: str = Field(default="", max_length=255)
    enabled: bool = False
    notes: str = ""


class ApiKeyTestRequest(BaseModel):
    provider: str
    provider_id: str = ""
    credential_type: str = "api_key"
    vault_reference: str = Field(default="", max_length=255)


class ProviderConfig(BaseModel):
    id: str
    name: str
    category: str
    source_id: str
    target_types: list[TargetType]
    status: Literal["ready", "stubbed", "needs_api_key", "disabled"]
    connector_function: str
    credential_refs: list[str] = Field(default_factory=list)
    admin_section: str
    proxy_route_supported: bool = False
    terms_note: str
    data_returned: list[str]
    note: str = ""


class SourceGate(BaseModel):
    source_id: str
    enabled: bool = False
    requires_approval: bool = True
    tenant_plan: str = "operator"
    note: str = ""


class ProxySettings(BaseModel):
    mode: Literal["off", "provider", "manual"] = "off"
    manual_entries: list[str] = Field(default_factory=list)
    use_only_for_allowlisted_egress: bool = True
    disable_failed_proxies: bool = True
    require_admin_approval: bool = False
    health_check_interval_minutes: int = 30


class ProxyImportRequest(BaseModel):
    entries_text: str = Field(default="", max_length=20000)


class ProxyRouteRule(BaseModel):
    id: str
    label: str
    category: str
    enabled: bool = False
    proxy_required: bool = False
    provider_ids: list[str] = Field(default_factory=list)
    allowed_domains: list[str] = Field(default_factory=list)
    note: str = ""


class ProxyTestResponse(BaseModel):
    ok: bool
    tested: int
    valid_format: int
    invalid_entries: list[str] = Field(default_factory=list)
    message: str


class ProxyConnectionTestRequest(BaseModel):
    entries: list[str] = Field(default_factory=list, max_length=200)
    target_url: str = Field(default="https://api.ipify.org?format=json", max_length=500)
    timeout_seconds: float = Field(default=8, ge=1, le=30)
    concurrency: int = Field(default=4, ge=1, le=10)


class ProxyConnectionResult(BaseModel):
    index: int
    proxy: str
    ok: bool
    status: Literal["connected", "failed", "invalid_format", "skipped"]
    latency_ms: float | None = None
    http_status: int | None = None
    error: str = ""
    target_url: str


class ProxyConnectionTestResponse(BaseModel):
    ok: bool
    tested: int
    connected: int
    failed: int
    target_url: str
    results: list[ProxyConnectionResult] = Field(default_factory=list)
    message: str


class PayPalCheckoutRequest(BaseModel):
    plan: str
    email: str | None = None


class PayPalCheckoutResponse(BaseModel):
    plan: str
    paypal_email: str
    checkout_url: str
    message: str


class ProviderRuntimeTestRequest(BaseModel):
    provider_id: str
    sample_target: str = "socialhunter"


class ProviderRuntimeTestResponse(BaseModel):
    provider_id: str
    ok: bool
    status: Literal["ready", "needs_key", "error", "skipped"]
    message: str
    latency_ms: float | None = None
    finding_count: int = 0


class WhatsMyNameImportRequest(BaseModel):
    dry_run: bool = True
    limit: int | None = Field(default=250, ge=1, le=10000)


class WhatsMyNameImportResponse(BaseModel):
    loaded: int = 0
    importable: int = 0
    dry_run: bool = True
    stored_total: int | None = None
    updated_at: str | None = None


class TenantAccount(BaseModel):
    id: str
    name: str
    plan: str = "growth"
    monthly_search_limit: int = 1500
    status: Literal["active", "pending", "suspended"] = "active"


class UserAccountView(BaseModel):
    username: str
    email: str
    role: Literal["admin", "member", "analyst", "billing", "viewer"]
    tenant_id: str
    plan: str
    active: bool = True
    failed_attempts: int = 0
    locked_until: str | None = None


class MemberDashboardSummary(BaseModel):
    user: UserAccountView
    tenant: TenantAccount
    plan: BillingPlan
    searches_this_month: int = 0
    reports_exported: int = 0
    enabled_sources: int = 0
    recent_jobs: list[SearchJob] = Field(default_factory=list)
    source_health: list[SourceHealth] = Field(default_factory=list)
    billing_status: str = "active"
    plan_features: list[str] = Field(default_factory=list)


class MailSettings(BaseModel):
    provider: str = "smtp_or_api"
    from_email: str = "support@spunwebtechnology.com"
    smtp_api_key_ref: str = "VAULT_REF_SOCIAL_HUNTER_SMTP_API_KEY"
    password_reset_enabled: bool = True
    contact_notifications_enabled: bool = True


class PayPalSettings(BaseModel):
    receiver_email: str = "techpronow@gmail.com"
    webhook_secret_ref: str = "VAULT_REF_PAYPAL_WEBHOOK_SECRET"
    subscriptions_enabled: bool = False
    webhook_verified: bool = False
    currency: str = "USD"
    checkout_mode: Literal["paypal_button", "subscription", "manual_invoice"] = "paypal_button"
    billing_contact_email: str = "techpronow@gmail.com"
    terms_url: str = "https://social-hunter.spunwebtechnology.com/#pricing"
    success_url: str = "https://social-hunter.spunwebtechnology.com/members/"
    cancel_url: str = "https://social-hunter.spunwebtechnology.com/#pricing"
    plans: list[BillingPlan] = Field(default_factory=lambda: [
        BillingPlan(
            id="starter",
            name="Starter",
            amount=49,
            monthly_search_limit=250,
            description="Entry plan for small public-source research workflows.",
            services=["250 searches per month", "Dashboard access", "JSON and CSV exports", "Public profile source gates"],
            paypal_item_name="Social Hunter Starter Plan",
            sort_order=10,
        ),
        BillingPlan(
            id="growth",
            name="Growth",
            amount=149,
            monthly_search_limit=1500,
            description="Team plan for recurring account, domain, and contact verification workflows.",
            services=["1,500 searches per month", "Member dashboard", "Report exports", "Provider health checks", "Source gate controls"],
            paypal_item_name="Social Hunter Growth Plan",
            sort_order=20,
        ),
        BillingPlan(
            id="operator",
            name="Operator",
            amount=399,
            monthly_search_limit=7500,
            api_access_enabled=True,
            description="Operator plan for higher-volume teams that need API access and advanced provider configuration.",
            services=["7,500 searches per month", "API access", "Advanced source controls", "Proxy route configuration", "Audit and compliance exports"],
            paypal_item_name="Social Hunter Operator Plan",
            sort_order=30,
        ),
    ])


class DeploymentHardeningStatus(BaseModel):
    https_only_cookies: bool = True
    csrf_required_for_admin: bool = True
    cors_locked_down: bool = True
    vault_only_secrets: bool = True
    container_health_checks: bool = True
    automated_backups: bool = False
    note: str = "Core hardening flags are configured; backup automation still requires host-level scheduling."
