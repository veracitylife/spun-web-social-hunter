"""Audit logging middleware for FastAPI."""
from fastapi import Request

from social_hunter.services.audit import AuditService


class AuditMiddleware:
    """Middleware to log all requests to audit trail."""

    def __init__(self, audit_service: AuditService):
        self.audit_service = audit_service

    async def log_request(self, request: Request, user_id: str, action: str) -> None:
        """Log a request to the audit trail."""
        # TODO: Wire to audit_service.log_event()
        pass
