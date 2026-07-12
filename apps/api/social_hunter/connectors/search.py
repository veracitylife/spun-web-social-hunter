from social_hunter.integrations.search_index import BraveSearchClient
from social_hunter.models import ComplianceFlag, Finding, FindingStatus, TargetType
from social_hunter.services.vault import resolve_vault_reference


def _brave_api_key() -> str | None:
    return (
        resolve_vault_reference("BRAVE_SEARCH_API_KEY_REF")
        or resolve_vault_reference("BRAVE_SEARCH_API_KEY_")
        or resolve_vault_reference("VAULT_REF_BRAVE_SEARCH_API_KEY")
    )


async def web_search_placeholder(target: str, target_type: TargetType) -> list[Finding]:
    if _brave_api_key():
        return await web_search_index_lookup(target)
    return [
        Finding(
            source="Search Index APIs",
            category="web_search",
            status=FindingStatus.skipped,
            confidence=0,
            title="Web search index enrichment not enabled",
            evidence=(
                f"Target {target} was not sent to Brave Search, SerpApi, Bing Web Search, Tavily, "
                f"Exa, or Google CSE. Configure a provider account before {target_type.value} search enrichment."
            ),
            compliance_flags=[ComplianceFlag.api_terms_required, ComplianceFlag.public_source, ComplianceFlag.no_raw_secret, ComplianceFlag.no_bypass],
        )
    ]


async def web_search_index_lookup(query: str) -> list[Finding]:
    key = _brave_api_key()
    if not key:
        return await web_search_placeholder(query, TargetType.domain)
    try:
        data = await BraveSearchClient(key).web_search(query)
    except Exception as exc:
        return [
            Finding(
                source="Brave Search API",
                category="web_search",
                status=FindingStatus.error,
                confidence=0,
                title="Brave Search API request failed",
                evidence=f"Brave Search request failed: {exc.__class__.__name__}. Verify Vault reference, account status, and rate limits.",
                compliance_flags=[ComplianceFlag.api_terms_required, ComplianceFlag.public_source, ComplianceFlag.no_raw_secret, ComplianceFlag.no_bypass],
            )
        ]
    results = data.get("web", {}).get("results", [])[:5]
    findings: list[Finding] = []
    for rank, item in enumerate(results, start=1):
        findings.append(
            Finding(
                source="Brave Search API",
                category="web_search",
                status=FindingStatus.found,
                confidence=max(0.45, 0.9 - rank * 0.06),
                title=item.get("title") or f"Brave Search result {rank}",
                url=item.get("url"),
                evidence=item.get("description") or "Public web search result returned by Brave Search API.",
                compliance_flags=[ComplianceFlag.api_terms_required, ComplianceFlag.public_source, ComplianceFlag.no_raw_secret, ComplianceFlag.no_bypass],
            )
        )
    if not findings:
        findings.append(
            Finding(
                source="Brave Search API",
                category="web_search",
                status=FindingStatus.not_found,
                confidence=0.7,
                title="No Brave Search results returned",
                evidence="Brave Search API returned no web results for the query.",
                compliance_flags=[ComplianceFlag.api_terms_required, ComplianceFlag.public_source, ComplianceFlag.no_raw_secret, ComplianceFlag.no_bypass],
            )
        )
    return findings
