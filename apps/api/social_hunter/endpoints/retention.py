"""Data retention and GDPR endpoints."""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from social_hunter.services.retention import RetentionService, RetentionPolicy, RetentionConfig

router = APIRouter(prefix="/api/settings/retention", tags=["settings"])


class SetRetentionPolicyRequest(BaseModel):
    """Request to set retention policy."""
    policy: RetentionPolicy


class ExportUserDataResponse(BaseModel):
    """Response for GDPR data export."""
    user_id: str
    searches_count: int
    exports_count: int
    audit_events_count: int
    generated_at: str


# Initialize retention service
retention_service = RetentionService()


@router.get("/policy", response_model=RetentionConfig)
async def get_retention_policy(user_id: str) -> RetentionConfig:
    """
    Get user's data retention policy.
    """
    return await retention_service.get_retention_policy(user_id)


@router.post("/policy")
async def set_retention_policy(user_id: str, request: SetRetentionPolicyRequest) -> RetentionConfig:
    """
    Set user's data retention policy.
    """
    return await retention_service.set_retention_policy(user_id, request.policy)


@router.post("/export-data", response_model=ExportUserDataResponse)
async def export_user_data(user_id: str) -> ExportUserDataResponse:
    """
    Generate a GDPR data export for the user.
    Returns all searches, exports, and audit logs.
    """
    data = await retention_service.export_user_data(user_id)
    return ExportUserDataResponse(
        user_id=user_id,
        searches_count=len(data.get("searches", [])),
        exports_count=len(data.get("exports", [])),
        audit_events_count=len(data.get("audit_events", [])),
        generated_at=data["generated_at"],
    )


@router.post("/delete-all-data")
async def delete_all_user_data(user_id: str) -> dict:
    """
    Permanently delete all user data (right to be forgotten).
    TODO: Require confirmation and admin approval.
    """
    deleted_count = await retention_service.delete_user_data(user_id)
    return {"status": "deleted", "user_id": user_id, "records_deleted": deleted_count}
