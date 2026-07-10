from social_hunter.models import ComplianceFlag, Finding, FindingStatus


async def phone_intel_placeholder(phone: str) -> list[Finding]:
    normalized = phone.strip()
    likely_phone = any(char.isdigit() for char in normalized) and len(normalized) >= 7
    return [
        Finding(
            source="Twilio Lookup v2",
            category="phone_intel",
            status=FindingStatus.skipped if likely_phone else FindingStatus.not_found,
            confidence=0 if likely_phone else 0.9,
            title="Phone validation and carrier intelligence not enabled",
            evidence=(
                "Phone syntax appears plausible. Map Vault-backed Twilio credentials before "
                "validating line type, carrier, caller name, SIM swap, reassigned-number, or risk signals."
                if likely_phone
                else "Input does not contain enough digits for a phone validation workflow."
            ),
            compliance_flags=[
                ComplianceFlag.api_terms_required,
                ComplianceFlag.no_raw_secret,
                ComplianceFlag.no_bypass,
            ],
        )
    ]
