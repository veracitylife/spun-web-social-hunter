from social_hunter.models import ComplianceFlag, Finding, FindingStatus, TargetType


async def web_search_placeholder(target: str, target_type: TargetType) -> list[Finding]:
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
            compliance_flags=[
                ComplianceFlag.api_terms_required,
                ComplianceFlag.public_source,
                ComplianceFlag.no_raw_secret,
                ComplianceFlag.no_bypass,
            ],
        )
    ]
