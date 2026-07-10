"""SQLAlchemy ORM models for production persistence.

These models are ready to be wired into the API endpoints.
You will need to:
1. Create Alembic migrations
2. Wire repositories into services
3. Replace in-memory stores with database queries
"""
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime, Float, Integer, Text, Boolean, Enum, ForeignKey, Table, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    """User account record."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    plan_id: Mapped[str] = mapped_column(String(50), default="free")
    roles: Mapped[list] = mapped_column(JSONB, default=[])
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    searches = relationship("SearchModel", back_populates="user")
    audit_events = relationship("AuditEventModel", back_populates="actor", foreign_keys="AuditEventModel.actor_id")
    retention_policy = relationship("RetentionPolicyModel", uselist=False, back_populates="user")


class SearchModel(Base):
    """Search record."""
    __tablename__ = "searches"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.id"), index=True)
    target_type: Mapped[str] = mapped_column(String(50), index=True)  # username, email, domain, ip
    target_hash: Mapped[str] = mapped_column(String(255), index=True)  # SHA256 hash for privacy
    status: Mapped[str] = mapped_column(String(50), default="completed")  # completed, failed, queued
    finding_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("UserModel", back_populates="searches")
    findings = relationship("FindingModel", back_populates="search", cascade="all, delete-orphan")
    exports = relationship("ExportModel", back_populates="search")


class FindingModel(Base):
    """Finding record (normalized search result)."""
    __tablename__ = "findings"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    search_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("searches.id"), index=True)
    source: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50))  # found, not_found, unknown, skipped, error
    confidence: Mapped[float] = mapped_column(Float)
    title: Mapped[str] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(String(500))
    evidence: Mapped[str] = mapped_column(Text)
    compliance_flags: Mapped[list] = mapped_column(JSONB, default=[])
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    search = relationship("SearchModel", back_populates="findings")


class ExportModel(Base):
    """Export record."""
    __tablename__ = "exports"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    search_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("searches.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(255), index=True)  # Denormalized for queries
    format: Mapped[str] = mapped_column(String(50))  # json, csv, markdown
    filename: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    search = relationship("SearchModel", back_populates="exports")


class AuditEventModel(Base):
    """Immutable audit event record."""
    __tablename__ = "audit_events"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    actor_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.id"), index=True)
    actor_email: Mapped[str | None] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(100), index=True)  # search:started, export:generated, etc.
    resource_type: Mapped[str] = mapped_column(String(100), index=True)
    resource_id: Mapped[str | None] = mapped_column(String(255), index=True)
    target_hash: Mapped[str | None] = mapped_column(String(255))
    target_type: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="success")  # success, failure, blocked
    ip_address: Mapped[str | None] = mapped_column(String(50))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    metadata: Mapped[dict] = mapped_column(JSONB, default={})
    error_detail: Mapped[str | None] = mapped_column(Text)

    actor = relationship("UserModel", back_populates="audit_events", foreign_keys="AuditEventModel.actor_id")


class RetentionPolicyModel(Base):
    """User data retention configuration."""
    __tablename__ = "retention_policies"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.id"), unique=True, index=True)
    policy: Mapped[str] = mapped_column(String(50), default="90_days")  # 30_days, 90_days, 180_days, 365_days, indefinite
    auto_delete_searches: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_delete_exports: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_delete_audit_logs: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("UserModel", back_populates="retention_policy")
