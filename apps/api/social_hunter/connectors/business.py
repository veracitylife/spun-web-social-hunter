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


async def google_places_business_lookup(query: str) -> list[Finding]:
    return [
        Finding(
            source="Google Places API",
            category="business_contact",
            status=FindingStatus.skipped,
            confidence=0,
            title="Google Places business lookup not enabled",
            evidence=(
                f"Business query {query} was not sent to Google Places. Configure the "
                "Vault-backed API key before using public business contact data."
            ),
            compliance_flags=[
                ComplianceFlag.public_source,
                ComplianceFlag.api_terms_required,
                ComplianceFlag.no_raw_secret,
                ComplianceFlag.no_bypass,
            ],
        )
    ]


async def yelp_fusion_business_lookup(query: str) -> list[Finding]:
    return [
        Finding(
            source="Yelp Fusion API",
            category="business_contact",
            status=FindingStatus.skipped,
            confidence=0,
            title="Yelp Fusion business lookup not enabled",
            evidence=(
                f"Business query {query} was not sent to Yelp Fusion. Configure the "
                "Vault-backed API key before using public local-business data."
            ),
            compliance_flags=[
                ComplianceFlag.public_source,
                ComplianceFlag.api_terms_required,
                ComplianceFlag.no_raw_secret,
                ComplianceFlag.no_bypass,
            ],
        )
    ]


async def opencorporates_company_lookup(company_name: str) -> list[Finding]:
    return [
        Finding(
            source="OpenCorporates",
            category="business_contact",
            status=FindingStatus.skipped,
            confidence=0,
            title="OpenCorporates company lookup not enabled",
            evidence=(
                f"Company {company_name} was not checked against OpenCorporates. This adapter "
                "is ready for public company-registry lookup with source attribution."
            ),
            compliance_flags=[
                ComplianceFlag.public_source,
                ComplianceFlag.no_raw_secret,
                ComplianceFlag.no_bypass,
            ],
        )
    ]
