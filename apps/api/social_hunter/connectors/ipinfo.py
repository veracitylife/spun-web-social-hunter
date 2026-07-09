from ipaddress import ip_address

from social_hunter.models import ComplianceFlag, Finding, FindingStatus


async def ipinfo_placeholder(ip: str) -> list[Finding]:
    try:
        ip_address(ip)
        status = FindingStatus.skipped
        confidence = 0
        evidence = "IP syntax is valid. IPinfo provider is not enabled until a Vault-backed token is mapped."
    except ValueError:
        status = FindingStatus.not_found
        confidence = 0.95
        evidence = "Input is not a valid IPv4 or IPv6 address."

    return [
        Finding(
            source="IPinfo",
            category="ip",
            status=status,
            confidence=confidence,
            title="IP intelligence lookup",
            evidence=evidence,
            compliance_flags=[
                ComplianceFlag.api_terms_required,
                ComplianceFlag.no_raw_secret,
                ComplianceFlag.no_bypass,
            ],
        )
    ]

