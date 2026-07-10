"""Audit logging endpoints for compliance and security."""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from social_hunter.services.audit import AuditService, AuditEvent, AuditActionType

router = APIRouter(prefix="/api/admin/audit", tags=["admin"])


class AuditLogQuery(BaseModel):
    """Query parameters for audit log retrieval."""
    actor_id: str | None = None
    action: AuditActionType | None = None
    limit: int = 100


class AuditLogResponse(BaseModel):
    """Audit log response."""
    events: list[AuditEvent]
    total_count: int


# Initialize audit service
audit_service = AuditService()


@router.get("/logs", response_model=AuditLogResponse)
async def get_audit_logs(query: AuditLogQuery) -> AuditLogResponse:
    """
    Retrieve audit logs (admin-only).
    TODO: Require admin role.
    """
    events = await audit_service.get_audit_log(
        actor_id=query.actor_id,
        action=query.action,
        limit=query.limit,
    )
    return AuditLogResponse(events=events, total_count=len(events))


@router.get("/logs/user/{user_id}", response_model=AuditLogResponse)
async def get_user_audit_logs(user_id: str, limit: int = 100) -> AuditLogResponse:
    """
    Get audit logs for a specific user (self or admin).
    """
    events = await audit_service.get_audit_log(actor_id=user_id, limit=limit)
    return AuditLogResponse(events=events, total_count=len(events))
