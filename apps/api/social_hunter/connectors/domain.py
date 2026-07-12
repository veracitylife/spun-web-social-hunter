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


async def rdap_domain_lookup(domain: str) -> list[Finding]:
    return [
        Finding(
            source="RDAP",
            category="domain_intel",
            status=FindingStatus.skipped,
            confidence=0,
            title="RDAP domain lookup not enabled",
            evidence=(
                f"Domain {domain} was not sent to RDAP in this dry-run adapter. Enable the "
                "public RDAP client before live domain checks."
            ),
            compliance_flags=[
                ComplianceFlag.public_source,
                ComplianceFlag.no_raw_secret,
                ComplianceFlag.no_bypass,
            ],
        )
    ]


async def securitytrails_domain_lookup(domain: str) -> list[Finding]:
    return [
        Finding(
            source="SecurityTrails",
            category="domain_intel",
            status=FindingStatus.skipped,
            confidence=0,
            title="SecurityTrails domain lookup not enabled",
            evidence=(
                f"Domain {domain} was not sent to SecurityTrails. Configure a Vault-backed "
                "API key before licensed DNS and infrastructure intelligence runs."
            ),
            compliance_flags=[
                ComplianceFlag.api_terms_required,
                ComplianceFlag.public_source,
                ComplianceFlag.no_raw_secret,
                ComplianceFlag.no_bypass,
            ],
        )
    ]


async def technology_profile_lookup(domain: str) -> list[Finding]:
    return [
        Finding(
            source="BuiltWith / Wappalyzer",
            category="domain_intel",
            status=FindingStatus.skipped,
            confidence=0,
            title="Technology profile lookup not enabled",
            evidence=(
                f"Domain {domain} was not sent to BuiltWith or Wappalyzer. Configure approved "
                "provider credentials before live technology profiling."
            ),
            compliance_flags=[
                ComplianceFlag.api_terms_required,
                ComplianceFlag.public_source,
                ComplianceFlag.no_raw_secret,
                ComplianceFlag.no_bypass,
            ],
        )
    ]


async def passive_dns_lookup(domain: str) -> list[Finding]:
    return [
        Finding(
            source="DNSDB-style passive DNS",
            category="domain_intel",
            status=FindingStatus.skipped,
            confidence=0,
            title="Passive DNS lookup not enabled",
            evidence=(
                f"Domain {domain} was not sent to a passive DNS provider. Configure licensed "
                "provider credentials and retention rules before enabling."
            ),
            compliance_flags=[
                ComplianceFlag.api_terms_required,
                ComplianceFlag.public_source,
                ComplianceFlag.no_raw_secret,
                ComplianceFlag.no_bypass,
            ],
        )
    ]
