from dataclasses import dataclass
from enum import Enum

import httpx


class ExistenceSignal(str, Enum):
    found = "found"
    not_found = "not_found"
    unknown = "unknown"
    error = "error"


@dataclass(frozen=True)
class ProfileCheckResult:
    source: str
    category: str
    url: str
    signal: ExistenceSignal
    confidence: float
    evidence: str
    status_code: int | None = None


@dataclass(frozen=True)
class ProfileSource:
    name: str
    category: str
    url_template: str
    expected_status: tuple[int, ...] = (200,)
    not_found_status: tuple[int, ...] = (404, 410)


class PublicProfileChecker:
    def __init__(self, timeout_seconds: float = 8.0, concurrency: int = 8) -> None:
        self.timeout_seconds = timeout_seconds
        self.concurrency = concurrency

    async def check_many(self, username: str, sources: list[ProfileSource]) -> list[ProfileCheckResult]:
        limits = httpx.Limits(max_connections=self.concurrency, max_keepalive_connections=self.concurrency)
        async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=True, limits=limits) as client:
            return [await self._check_one(client, username, source) for source in sources]

    async def _check_one(self, client: httpx.AsyncClient, username: str, source: ProfileSource) -> ProfileCheckResult:
        url = source.url_template.replace("{account}", username)
        try:
            response = await client.get(url, headers={"User-Agent": "SocialHunterEducational/0.1"})
        except httpx.HTTPError as exc:
            return ProfileCheckResult(
                source=source.name,
                category=source.category,
                url=url,
                signal=ExistenceSignal.error,
                confidence=0.0,
                evidence=f"HTTP request failed: {exc.__class__.__name__}",
            )

        if response.status_code in source.expected_status:
            signal = ExistenceSignal.found
            confidence = 0.78
            evidence = f"Public URL returned HTTP {response.status_code}."
        elif response.status_code in source.not_found_status:
            signal = ExistenceSignal.not_found
            confidence = 0.72
            evidence = f"Public URL returned HTTP {response.status_code}."
        else:
            signal = ExistenceSignal.unknown
            confidence = 0.35
            evidence = f"Public URL returned inconclusive HTTP {response.status_code}."

        return ProfileCheckResult(
            source=source.name,
            category=source.category,
            url=url,
            signal=signal,
            confidence=confidence,
            evidence=evidence,
            status_code=response.status_code,
        )
