"""Data retention and cleanup service for account-level GDPR/privacy compliance."""
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class RetentionPolicy(str, Enum):
    """Retention policy presets."""
    DAYS_30 = "30_days"
    DAYS_90 = "90_days"
    DAYS_180 = "180_days"
    DAYS_365 = "365_days"
    INDEFINITE = "indefinite"


class RetentionConfig(BaseModel):
    """User-configurable data retention settings."""
    user_id: str
    policy: RetentionPolicy = RetentionPolicy.DAYS_90
    auto_delete_searches: bool = True
    auto_delete_exports: bool = True
    auto_delete_audit_logs: bool = False  # Usually required for compliance
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def retention_days(self) -> Optional[int]:
        """Return retention period in days, or None if indefinite."""
        policy_map = {
            RetentionPolicy.DAYS_30: 30,
            RetentionPolicy.DAYS_90: 90,
            RetentionPolicy.DAYS_180: 180,
            RetentionPolicy.DAYS_365: 365,
            RetentionPolicy.INDEFINITE: None,
        }
        return policy_map.get(self.policy)


class RetentionService:
    """Manages data retention policies, expiration, and automated cleanup."""

    def __init__(self, db_session=None):
        self.db_session = db_session
        self.user_policies: dict[str, RetentionConfig] = {}  # In-memory cache (demo)

    async def set_retention_policy(self, user_id: str, policy: RetentionPolicy) -> RetentionConfig:
        """Set retention policy for a user."""
        config = RetentionConfig(
            user_id=user_id,
            policy=policy,
            updated_at=datetime.now(timezone.utc),
        )
        # TODO: Wire SQLAlchemy to persist to retention_policies table
        self.user_policies[user_id] = config
        return config

    async def get_retention_policy(self, user_id: str) -> RetentionConfig:
        """Get user's retention policy (or default)."""
        return self.user_policies.get(user_id) or RetentionConfig(
            user_id=user_id,
            policy=RetentionPolicy.DAYS_90,
        )

    async def should_delete_search(self, user_id: str, search_created_at: datetime) -> bool:
        """Check if a search should be deleted based on retention policy."""
        config = await self.get_retention_policy(user_id)
        retention_days = config.retention_days()

        if retention_days is None or not config.auto_delete_searches:
            return False

        now = datetime.now(timezone.utc)
        age = now - search_created_at
        return age > timedelta(days=retention_days)

    async def should_delete_export(self, user_id: str, export_created_at: datetime) -> bool:
        """Check if an export should be deleted based on retention policy."""
        config = await self.get_retention_policy(user_id)
        retention_days = config.retention_days()

        if retention_days is None or not config.auto_delete_exports:
            return False

        now = datetime.now(timezone.utc)
        age = now - export_created_at
        return age > timedelta(days=retention_days)

    async def cleanup_expired_searches(self) -> int:
        """
        Scan all searches and delete those past retention period.
        Returns count of deleted searches.
        Scheduled as a background task (e.g., nightly via Celery).
        """
        # TODO: Implement database scan and deletion
        # SELECT searches WHERE created_at < NOW() - retention_days
        # DELETE FROM searches WHERE id IN (...)
        # DELETE FROM findings WHERE search_id IN (...)
        deleted_count = 0
        return deleted_count

    async def cleanup_expired_exports(self) -> int:
        """
        Scan all exports and delete those past retention period.
        Returns count of deleted exports.
        """
        # TODO: Implement database scan and deletion
        deleted_count = 0
        return deleted_count

    async def export_user_data(self, user_id: str) -> dict:
        """
        Generate a GDPR data export for a user (all searches, exports, audit logs).
        Returns dict with data.
        """
        # TODO: Query all user searches, exports, audit events
        return {
            "user_id": user_id,
            "searches": [],
            "exports": [],
            "audit_events": [],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def delete_user_data(self, user_id: str) -> int:
        """
        Permanently delete all user data (right to be forgotten).
        Returns count of deleted records.
        """
        # TODO: Implement cascading deletion
        # DELETE FROM searches WHERE user_id = ...
        # DELETE FROM exports WHERE user_id = ...
        # DELETE FROM audit_events WHERE actor_id = ...
        deleted_count = 0
        return deleted_count
