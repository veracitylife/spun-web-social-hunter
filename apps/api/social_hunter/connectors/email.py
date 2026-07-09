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

