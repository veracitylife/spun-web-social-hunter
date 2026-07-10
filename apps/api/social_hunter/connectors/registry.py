from social_hunter.connectors.breach import breach_placeholder
from social_hunter.connectors.email import email_validation_placeholder
from social_hunter.connectors.ipinfo import ipinfo_placeholder
from social_hunter.connectors.username import username_lookup
from social_hunter.models import Finding, SearchRequest, TargetType


async def run_connectors(request: SearchRequest) -> list[Finding]:
    findings: list[Finding] = []

    if request.target_type == TargetType.username:
        findings.extend(await username_lookup(request.target))

    if request.target_type == TargetType.email:
        findings.extend(await breach_placeholder(request.target))
        findings.extend(await email_validation_placeholder(request.target))

    if request.target_type == TargetType.ip:
        findings.extend(await ipinfo_placeholder(request.target))

    if request.target_type == TargetType.domain:
        findings.append(
            Finding(
                source="domain-intelligence",
                category="domain",
                status="skipped",
                confidence=0,
                title="Domain intelligence not configured",
                evidence="Wire a licensed DNS/WHOIS provider before enabling domain lookups.",
                compliance_flags=["api_terms_required", "no_bypass"],
            )
        )

    return findings
