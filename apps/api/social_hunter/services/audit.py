"""Immutable audit logging service for search, export, and admin actions."""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AuditActionType(str, Enum):
    """Audit event action types."""
    SEARCH_STARTED = "search:started"
    SEARCH_COMPLETED = "search:completed"
    SEARCH_FAILED = "search:failed"
    EXPORT_GENERATED = "export:generated"
    EXPORT_DOWNLOADED = "export:downloaded"
    SOURCE_ENABLED = "source:enabled"
    SOURCE_DISABLED = "source:disabled"
    PLAN_CHANGED = "plan:changed"
    API_KEY_ROTATED = "api_key:rotated"
    USER_LOGIN = "user:login"
    USER_LOGOUT = "user:logout"
    ADMIN_ACTION = "admin:action"
    TARGET_DENIED = "target:denied"
    RATE_LIMIT_EXCEEDED = "rate_limit:exceeded"
    COMPLIANCE_CHECK_FAILED = "compliance:check_failed"


class AuditEvent(BaseModel):
    """Immutable audit log entry."""
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor_id: str  # user_id or "system"
    actor_email: Optional[str] = None
    action: AuditActionType
    resource_type: str  # "search", "export", "source", etc.
    resource_id: Optional[str] = None
    target_hash: Optional[str] = None  # hashed target for privacy (not searchable PII)
    target_type: Optional[str] = None  # "username", "email", "domain", "ip"
    status: str = "success"  # "success", "failure", "blocked"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)  # source_set, export_format, etc.
    error_detail: Optional[str] = None  # If status == "failure"


class AuditService:
    """Manages immutable audit logs for compliance and security."""

    def __init__(self, db_session=None, redis_client=None):
        """
        Initialize audit service with optional database and cache backends.
        db_session: SQLAlchemy async session for persistent storage
        redis_client: Redis client for real-time audit streaming
        """
        self.db_session = db_session
        self.redis_client = redis_client
        self.in_memory_log: list[AuditEvent] = []  # Fallback for demo

    async def log_event(self, event: AuditEvent) -> str:
        """Log an audit event. Returns event ID."""
        # TODO: Wire SQLAlchemy repository to persist to audit_events table
        if self.db_session:
            # await self.db_session.execute(
            #     insert(AuditEventModel).values(event.model_dump())
            # )
            # await self.db_session.commit()
            pass

        # TODO: Publish to Redis for real-time audit streaming
        if self.redis_client:
            # await self.redis_client.publish(
            #     "audit:events",
            #     event.model_dump_json()
            # )
            pass

        # Fallback: store in-memory for demo
        self.in_memory_log.append(event)
        return str(event.id)

    async def search_started(self, actor_id: str, target_type: str, target_hash: str, source_set: list[str], **kwargs) -> str:
        """Log a search initiation."""
        event = AuditEvent(
            actor_id=actor_id,
            action=AuditActionType.SEARCH_STARTED,
            resource_type="search",
            target_type=target_type,
            target_hash=target_hash,
            metadata={"source_set": source_set},
            **kwargs,
        )
        return await self.log_event(event)

    async def search_completed(self, actor_id: str, search_id: str, finding_count: int, **kwargs) -> str:
        """Log a successful search."""
        event = AuditEvent(
            actor_id=actor_id,
            action=AuditActionType.SEARCH_COMPLETED,
            resource_type="search",
            resource_id=search_id,
            status="success",
            metadata={"finding_count": finding_count},
            **kwargs,
        )
        return await self.log_event(event)

    async def search_failed(self, actor_id: str, target_type: str, error: str, **kwargs) -> str:
        """Log a failed search."""
        event = AuditEvent(
            actor_id=actor_id,
            action=AuditActionType.SEARCH_FAILED,
            resource_type="search",
            target_type=target_type,
            status="failure",
            error_detail=error,
            **kwargs,
        )
        return await self.log_event(event)

    async def export_generated(self, actor_id: str, search_id: str, export_format: str, **kwargs) -> str:
        """Log an export generation."""
        event = AuditEvent(
            actor_id=actor_id,
            action=AuditActionType.EXPORT_GENERATED,
            resource_type="export",
            resource_id=search_id,
            metadata={"format": export_format},
            **kwargs,
        )
        return await self.log_event(event)

    async def target_denied(self, actor_id: str, target: str, reason: str, **kwargs) -> str:
        """Log a denied target (compliance block)."""
        event = AuditEvent(
            actor_id=actor_id,
            action=AuditActionType.TARGET_DENIED,
            resource_type="search",
            status="blocked",
            error_detail=reason,
            metadata={"reason": reason},
            **kwargs,
        )
        return await self.log_event(event)

    async def rate_limit_exceeded(self, actor_id: str, limit_type: str, **kwargs) -> str:
        """Log a rate limit violation."""
        event = AuditEvent(
            actor_id=actor_id,
            action=AuditActionType.RATE_LIMIT_EXCEEDED,
            resource_type="rate_limit",
            status="blocked",
            metadata={"limit_type": limit_type},
            **kwargs,
        )
        return await self.log_event(event)

    async def get_audit_log(self, actor_id: Optional[str] = None, action: Optional[AuditActionType] = None, limit: int = 100) -> list[AuditEvent]:
        """Retrieve audit log entries (demo only; production uses database queries)."""
        # TODO: Implement filtered database query
        results = self.in_memory_log
        if actor_id:
            results = [e for e in results if e.actor_id == actor_id]
        if action:
            results = [e for e in results if e.action == action]
        return results[-limit:]
