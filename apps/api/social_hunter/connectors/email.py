from email_validator import EmailNotValidError, validate_email

from social_hunter.models import ComplianceFlag, Finding, FindingStatus


async def email_validation_placeholder(email: str) -> list[Finding]:
    try:
        validate_email(email, check_deliverability=False)
        status = FindingStatus.found
        confidence = 0.72
        evidence = "Email syntax is valid. Deliverability and enrichment providers are not enabled."
    except EmailNotValidError as exc:
        status = FindingStatus.not_found
        confidence = 0.9
        evidence = f"Email syntax validation failed: {exc}"

    return [
        Finding(
            source="local-email-validator",
            category="email",
            status=status,
            confidence=confidence,
            title="Email syntax validation",
            evidence=evidence,
            compliance_flags=[
                ComplianceFlag.public_source,
                ComplianceFlag.no_raw_secret,
                ComplianceFlag.no_bypass,
            ],
        )
    ]


async def email_validation_lookup(email: str) -> list[Finding]:
    return await email_validation_placeholder(email)


async def hunter_email_intel_lookup(email_or_domain: str) -> list[Finding]:
    return [
        Finding(
            source="Hunter.io",
            category="email_intel",
            status=FindingStatus.skipped,
            confidence=0,
            title="Hunter.io email discovery and verification not enabled",
            evidence=(
                f"Target {email_or_domain} was not sent to Hunter.io. Add a Vault-backed "
                "Hunter API key and keep domain/email discovery behind the consent controls."
            ),
            compliance_flags=[
                ComplianceFlag.api_terms_required,
                ComplianceFlag.user_authorized,
                ComplianceFlag.no_raw_secret,
                ComplianceFlag.no_bypass,
            ],
        )
    ]


async def hibp_breach_exposure_lookup(email: str) -> list[Finding]:
    return [
        Finding(
            source="Have I Been Pwned",
            category="email_intel",
            status=FindingStatus.skipped,
            confidence=0,
            title="HIBP breach exposure lookup not enabled",
            evidence=(
                f"Email {email} was not sent to HIBP. Configure a Vault-backed HIBP API key "
                "and use this only for exposure reporting and account-risk education."
            ),
            compliance_flags=[
                ComplianceFlag.api_terms_required,
                ComplianceFlag.user_authorized,
                ComplianceFlag.no_raw_secret,
                ComplianceFlag.no_bypass,
            ],
        )
    ]
