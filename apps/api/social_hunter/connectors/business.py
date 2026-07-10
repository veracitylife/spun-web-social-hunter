from social_hunter.models import ComplianceFlag, Finding, FindingStatus


async def business_contact_placeholder(domain: str) -> list[Finding]:
    return [
        Finding(
            source="Business / Local Contact Data",
            category="business_contact",
            status=FindingStatus.skipped,
            confidence=0,
            title="Business contact data not enabled",
            evidence=(
                f"Domain {domain} was not sent to Google Places, Yelp Fusion, or OpenCorporates. "
                "Enable only public business/entity data providers and avoid private-person contact discovery."
            ),
            compliance_flags=[
                ComplianceFlag.api_terms_required,
                ComplianceFlag.public_source,
                ComplianceFlag.no_raw_secret,
                ComplianceFlag.no_bypass,
            ],
        )
    ]
