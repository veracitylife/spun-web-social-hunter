from social_hunter.models import ComplianceFlag, Finding, FindingStatus


async def domain_intel_placeholder(domain: str) -> list[Finding]:
    return [
        Finding(
            source="WHOIS / RDAP",
            category="domain_intel",
            status=FindingStatus.skipped,
            confidence=0,
            title="Domain and infrastructure intelligence not enabled",
            evidence=(
                f"Domain {domain} was not sent to RDAP, SecurityTrails, BuiltWith, Wappalyzer, "
                "or passive DNS providers. Wire approved providers before live infrastructure lookups."
            ),
            compliance_flags=[
                ComplianceFlag.public_source,
                ComplianceFlag.api_terms_required,
                ComplianceFlag.no_raw_secret,
                ComplianceFlag.no_bypass,
            ],
        )
    ]
