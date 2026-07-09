from datetime import datetime, timezone

from social_hunter.models import SourceHealth
from social_hunter.sources import SOURCE_CAPABILITIES


def get_source_health() -> list[SourceHealth]:
    health: list[SourceHealth] = []
    for source in SOURCE_CAPABILITIES:
        if source.status == "ready":
            status = "healthy"
            note = "Enabled source is ready."
            latency = 50.0
        elif source.status == "needs_api_key":
            status = "needs_key"
            note = "Provider credentials must be mapped from Vault before live calls."
            latency = None
        elif source.status == "disabled":
            status = "disabled"
            note = "Disabled until an approved normalized-results engine is connected."
            latency = None
        else:
            status = "degraded"
            note = "Stubbed for classroom/demo use."
            latency = 0.0
        health.append(SourceHealth(
            source_id=source.id,
            status=status,
            latency_ms=latency,
            last_checked_at=datetime.now(timezone.utc),
            note=note,
        ))
    return health
