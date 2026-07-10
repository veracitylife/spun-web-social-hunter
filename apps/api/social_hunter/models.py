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


class PlanResponse(BaseModel):
    id: str
    name: str
    monthly_search_limit: int
    export_enabled: bool
    api_access_enabled: bool


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
