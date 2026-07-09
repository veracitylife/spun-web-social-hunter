from social_hunter.models import ComplianceFlag, Finding, FindingStatus


async def breach_placeholder(email: str) -> list[Finding]:
    return [
        Finding(
            source="Have I Been Pwned",
            category="breach",
            status=FindingStatus.skipped,
            confidence=0,
            title="HIBP breach lookup not enabled",
            evidence=(
                f"Target {email} was not sent to HIBP. Add a Vault-backed API key and terms review "
                "before enabling live breach lookup."
            ),
            compliance_flags=[
                ComplianceFlag.api_terms_required,
                ComplianceFlag.no_raw_secret,
                ComplianceFlag.no_bypass,
            ],
        )
    ]

