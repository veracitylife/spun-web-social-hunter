from social_hunter.connectors.breach import breach_placeholder
from social_hunter.connectors.business import business_contact_placeholder
from social_hunter.connectors.domain import domain_intel_placeholder
from social_hunter.connectors.email import email_validation_placeholder
from social_hunter.connectors.ipinfo import ipinfo_placeholder
from social_hunter.connectors.person import person_enrichment_placeholder
from social_hunter.connectors.phone import phone_intel_placeholder
from social_hunter.connectors.search import web_search_placeholder
from social_hunter.connectors.username import github_user_lookup, username_lookup
from social_hunter.models import Finding, SearchRequest, TargetType


async def run_connectors(request: SearchRequest) -> list[Finding]:
    findings: list[Finding] = []
    groups = set(request.source_groups)

    if request.target_type == TargetType.username and "username_profile" in groups:
        findings.extend(await username_lookup(request.target))
        findings.extend(await github_user_lookup(request.target))
        if "web_search" in groups:
            findings.extend(await web_search_placeholder(request.target, request.target_type))

    if request.target_type == TargetType.email:
        if "breach" in groups or "email_intel" in groups:
            findings.extend(await breach_placeholder(request.target))
        if "email_intel" in groups:
            findings.extend(await email_validation_placeholder(request.target))
        if "person_enrichment" in groups:
            findings.extend(await person_enrichment_placeholder(request.target, request.target_type))
        if "web_search" in groups:
            findings.extend(await web_search_placeholder(request.target, request.target_type))

    if request.target_type == TargetType.ip:
        if "ip" in groups or "domain_intel" in groups:
            findings.extend(await ipinfo_placeholder(request.target))
        if "person_enrichment" in groups:
            findings.extend(await person_enrichment_placeholder(request.target, request.target_type))

    if request.target_type == TargetType.domain:
        if "email_intel" in groups:
            findings.extend(await email_validation_placeholder(f"contact@{request.target}"))
        if "business_contact" in groups:
            findings.extend(await business_contact_placeholder(request.target))
        if "domain_intel" in groups:
            findings.extend(await domain_intel_placeholder(request.target))
        if "web_search" in groups:
            findings.extend(await web_search_placeholder(request.target, request.target_type))
        if "person_enrichment" in groups:
            findings.extend(await person_enrichment_placeholder(request.target, request.target_type))

    if request.target_type == TargetType.phone and "phone_intel" in groups:
        findings.extend(await phone_intel_placeholder(request.target))

    return findings
