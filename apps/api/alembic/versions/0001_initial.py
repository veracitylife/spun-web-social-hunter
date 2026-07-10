"""Initial migration - create core tables.

Revision ID: 0001
Revises:
Create Date: 2025-01-09 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create search_records table
    op.create_table(
        "search_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(255), nullable=False, index=True),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_hash", sa.String(64), nullable=False, index=True),
        sa.Column("target_preview", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, default="queued"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True, default={}),
    )

    # Create finding_records table
    op.create_table(
        "finding_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("search_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("search_records.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("source", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("compliance_flags", postgresql.JSONB(), nullable=True, default=[]),
    )


    # Create source_capability_records table
    op.create_table(
        "source_capability_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_id", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("target_types", postgresql.JSONB(), nullable=True, default=[]),
        sa.Column("status", sa.String(50), nullable=False, default="stubbed"),
        sa.Column("terms_note", sa.Text(), nullable=True),
        sa.Column("data_returned", postgresql.JSONB(), nullable=True, default=[]),
        sa.Column("raw_payload_storage_allowed", sa.Boolean(), nullable=False, default=False),
        sa.Column("config", postgresql.JSONB(), nullable=True, default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    # Create source_health_records table
    op.create_table(
        "source_health_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", sa.String(255), nullable=False, unique=True),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Create export_records table
    op.create_table(
        "export_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(255), nullable=False, index=True),
        sa.Column("search_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("search_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("format", sa.String(50), nullable=False),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True, default={}),
    )

    # Create audit_records table
    op.create_table(
        "audit_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor", sa.String(255), nullable=False, index=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=True),
        sa.Column("target_hash", sa.String(64), nullable=True, index=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True, default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, index=True),
    )

    # Create indexes for common queries
    op.create_index("ix_search_records_user_created", "search_records", ["user_id", "created_at"])
    op.create_index("ix_finding_records_source_status", "finding_records", ["source", "status"])


def downgrade() -> None:
    op.drop_table("audit_records")
    op.drop_table("export_records")
    op.drop_table("source_health_records")
    op.drop_table("source_capability_records")
    op.drop_table("finding_records")
    op.drop_table("search_records")
