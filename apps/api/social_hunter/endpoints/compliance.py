"""Compliance and denylisting admin endpoints."""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from social_hunter.services.compliance import ComplianceService, ComplianceConfig, ComplianceCheckResult

router = APIRouter(prefix="/api/admin/compliance", tags=["admin"])


class ComplianceCheckRequest(BaseModel):
    """Request to check compliance for a target."""
    target_type: str
    target: str


class UpdateDenylistRequest(BaseModel):
    """Request to update denylists."""
    action: str  # "add", "remove"
    category: str  # "email_patterns", "domains", "ips", etc.
    value: str


# Initialize compliance service
config = ComplianceConfig()
compliance_service = ComplianceService(config)


@router.post("/check", response_model=ComplianceCheckResult)
async def check_compliance(request: ComplianceCheckRequest) -> ComplianceCheckResult:
    """
    Check if a target passes compliance rules.
    Admin/audit endpoint for testing denylists.
    """
    result = await compliance_service.check_compliance(request.target_type, request.target)
    return result


@router.post("/denylist/update")
async def update_denylist(request: UpdateDenylistRequest) -> dict:
    """
    Update denylists (email patterns, domains, IPs).
    TODO: Require admin role and audit logging.
    """
    if request.action == "add":
        if request.category == "email_patterns":
            if request.value not in compliance_service.config.blocked_email_patterns:
                compliance_service.config.blocked_email_patterns.append(request.value)
        elif request.category == "domains":
            if request.value not in compliance_service.config.blocked_domains:
                compliance_service.config.blocked_domains.append(request.value)
        elif request.category == "ips":
            if request.value not in compliance_service.config.blocked_ips:
                compliance_service.config.blocked_ips.append(request.value)
    elif request.action == "remove":
        if request.category == "email_patterns" and request.value in compliance_service.config.blocked_email_patterns:
            compliance_service.config.blocked_email_patterns.remove(request.value)
        elif request.category == "domains" and request.value in compliance_service.config.blocked_domains:
            compliance_service.config.blocked_domains.remove(request.value)
        elif request.category == "ips" and request.value in compliance_service.config.blocked_ips:
            compliance_service.config.blocked_ips.remove(request.value)

    return {"status": "updated", "category": request.category, "action": request.action}


@router.get("/denylist")
async def get_denylists() -> dict:
    """
    Get current denylists (email patterns, domains, IPs).
    """
    return {
        "blocked_email_patterns": compliance_service.config.blocked_email_patterns,
        "blocked_domains": compliance_service.config.blocked_domains,
        "blocked_ips": compliance_service.config.blocked_ips,
    }
