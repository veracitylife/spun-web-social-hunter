from social_hunter.models import ComplianceFlag, Finding, FindingStatus, TargetType


async def person_enrichment_placeholder(target: str, target_type: TargetType) -> list[Finding]:
    return [
        Finding(
            source="People Data Labs",
            category="person_enrichment",
            status=FindingStatus.skipped,
            confidence=0,
            title="Person/company enrichment not enabled",
            evidence=(
                f"Target {target} was not sent to a person-enrichment provider. Map licensed "
                f"Vault-backed credentials and require consent or legitimate-interest review before "
                f"running {target_type.value} enrichment."
            ),
            compliance_flags=[
                ComplianceFlag.api_terms_required,
                ComplianceFlag.user_authorized,
                ComplianceFlag.no_raw_secret,
                ComplianceFlag.no_bypass,
            ],
        )
    ]


async def people_data_labs_enrichment(target: str, target_type: TargetType = TargetType.email) -> list[Finding]:
    return await person_enrichment_placeholder(target, target_type)


async def fullcontact_style_enrichment_slot(target: str, target_type: TargetType = TargetType.email) -> list[Finding]:
    return [
        Finding(
            source="FullContact-style licensed enrichment",
            category="person_enrichment",
            status=FindingStatus.skipped,
            confidence=0,
            title="Reserved enrichment provider slot",
            evidence=(
                f"Target {target} was not sent to a FullContact-style enrichment provider. "
                "Add licensed provider credentials through Vault references before live enrichment."
            ),
            compliance_flags=[
                ComplianceFlag.api_terms_required,
                ComplianceFlag.user_authorized,
                ComplianceFlag.no_raw_secret,
                ComplianceFlag.no_bypass,
            ],
        )
    ]
