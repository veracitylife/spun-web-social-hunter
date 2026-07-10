"""PostgreSQL repository for search operations."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from social_hunter.db import FindingRecord, SearchRecord
from social_hunter.models import Finding, SearchJob, SearchRequest, SearchResponse


class SearchRepository:
    """Repository for persisting searches and findings."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_search(
        self,
        user_id: str,
        request: SearchRequest,
        job: SearchJob,
    ) -> SearchRecord:
        """Create a new search record."""
        from social_hunter.utils.hashing import hash_target

        record = SearchRecord(
            id=job.id,
            user_id=user_id,
            target_type=request.target_type.value,
            target_hash=hash_target(request.target),
            target_preview=request.target[:100],
            status="queued",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            metadata_json={
                "source_groups": request.source_groups,
                "consent_confirmed": request.consent_confirmed,
            },
        )
        self.session.add(record)
        await self.session.commit()
        return record

    async def update_search_status(
        self,
        search_id: UUID,
        status: str,
        error_message: str | None = None,
    ) -> None:
        """Update search status."""
        record = await self.session.get(SearchRecord, search_id)
        if record:
            record.status = status
            record.updated_at = datetime.now(timezone.utc)
            if status in ("completed", "failed"):
                record.completed_at = datetime.now(timezone.utc)
            if error_message:
                record.error_message = error_message
            await self.session.commit()

    async def save_findings(
        self,
        search_id: UUID,
        findings: list[Finding],
    ) -> None:
        """Persist findings for a search."""
        for finding in findings:
            record = FindingRecord(
                id=finding.id,
                search_id=search_id,
                source=finding.source,
                category=finding.category,
                status=finding.status.value,
                confidence=finding.confidence,
                title=finding.title,
                url=str(finding.url) if finding.url else None,
                evidence=finding.evidence,
                checked_at=finding.checked_at,
                compliance_flags=[f.value for f in finding.compliance_flags],
            )
            self.session.add(record)
        await self.session.commit()

    async def get_search_with_findings(
        self,
        search_id: UUID,
    ) -> tuple[SearchRecord, list[FindingRecord]] | None:
        """Retrieve a search with all its findings."""
        result = await self.session.execute(
            select(SearchRecord).where(SearchRecord.id == search_id)
        )
        search = result.scalar_one_or_none()
        if not search:
            return None

        findings_result = await self.session.execute(
            select(FindingRecord).where(FindingRecord.search_id == search_id)
        )
        findings = findings_result.scalars().all()

        return search, list(findings)

    async def list_user_searches(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[SearchRecord]:
        """List searches for a user."""
        result = await self.session.execute(
            select(SearchRecord)
            .where(SearchRecord.user_id == user_id)
            .order_by(SearchRecord.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
