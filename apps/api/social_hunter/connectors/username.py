import json
from pathlib import Path

from social_hunter.integrations.public_profiles import GitHubUsersClient
from social_hunter.models import ComplianceFlag, Finding, FindingStatus
from social_hunter.services.vault import resolve_vault_reference

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "sources.json"


def _github_token() -> str | None:
    return resolve_vault_reference("GITHUB_TOKEN_REF") or resolve_vault_reference("VAULT_REF_GITHUB_TOKEN")


async def username_lookup(username: str) -> list[Finding]:
    sources = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    normalized = username.strip().lstrip("@")
    findings: list[Finding] = []

    for source in sources["username_sources"]:
        profile_url = source["url"].replace("{account}", normalized)
        simulated_found = normalized.lower() in source.get("demo_found_for", [])
        imported = source.get("imported_from") == "WhatsMyName"
        findings.append(
            Finding(
                source=source["name"],
                category=source["category"],
                status=FindingStatus.found if simulated_found else FindingStatus.unknown,
                confidence=0.86 if simulated_found else 0.42 if imported else 0.35,
                title=f"{source['name']} profile URL",
                url=profile_url,
                evidence=(
                    "WhatsMyName dataset generated this public profile URL. Live existence checks remain disabled by default."
                    if imported and not simulated_found
                    else "Demo fixture indicates a likely public profile."
                    if simulated_found
                    else "Local dataset generated the public profile URL; live HTTP existence check is not enabled."
                ),
                compliance_flags=[
                    ComplianceFlag.public_source,
                    ComplianceFlag.no_bypass,
                    ComplianceFlag.no_raw_secret,
                ],
            )
        )

    return findings


async def github_user_lookup(username: str) -> list[Finding]:
    normalized = username.strip().lstrip("@")
    if not normalized:
        return []
    try:
        data = await GitHubUsersClient(_github_token()).user(normalized)
    except Exception as exc:
        return [
            Finding(
                source="GitHub REST Users API",
                category="username_profile",
                status=FindingStatus.error,
                confidence=0,
                title="GitHub public profile lookup failed",
                url=f"https://github.com/{normalized}",
                evidence=f"GitHub API request failed: {exc.__class__.__name__}. Token is optional but can improve rate limits.",
                compliance_flags=[ComplianceFlag.public_source, ComplianceFlag.api_terms_required, ComplianceFlag.no_raw_secret, ComplianceFlag.no_bypass],
            )
        ]
    if not data:
        return [
            Finding(
                source="GitHub REST Users API",
                category="username_profile",
                status=FindingStatus.not_found,
                confidence=0.82,
                title="GitHub public profile not found",
                url=f"https://github.com/{normalized}",
                evidence="GitHub API returned 404 for this public username.",
                compliance_flags=[ComplianceFlag.public_source, ComplianceFlag.api_terms_required, ComplianceFlag.no_raw_secret, ComplianceFlag.no_bypass],
            )
        ]
    profile_url = data.get("html_url") or f"https://github.com/{normalized}"
    public_bits = []
    for key in ["name", "company", "blog", "location", "public_repos", "followers"]:
        value = data.get(key)
        if value not in (None, ""):
            public_bits.append(f"{key}: {value}")
    return [
        Finding(
            source="GitHub REST Users API",
            category="username_profile",
            status=FindingStatus.found,
            confidence=0.95,
            title="GitHub public profile found",
            url=profile_url,
            evidence="Public GitHub profile metadata: " + ("; ".join(public_bits) if public_bits else "profile exists"),
            compliance_flags=[ComplianceFlag.public_source, ComplianceFlag.api_terms_required, ComplianceFlag.no_raw_secret, ComplianceFlag.no_bypass],
        )
    ]


async def reddit_profile_lookup(username: str) -> list[Finding]:
    normalized = username.strip().removeprefix("u/").lstrip("@")
    return [
        Finding(
            source="Reddit API",
            category="username_profile",
            status=FindingStatus.skipped,
            confidence=0,
            title="Reddit public profile lookup not enabled",
            url=f"https://www.reddit.com/user/{normalized}/" if normalized else None,
            evidence=(
                "Reddit username lookup is wired to this adapter. Enable approved Reddit API "
                "credentials before live public profile metadata checks."
            ),
            compliance_flags=[ComplianceFlag.public_source, ComplianceFlag.api_terms_required, ComplianceFlag.no_raw_secret, ComplianceFlag.no_bypass],
        )
    ]


async def x_user_lookup(username: str) -> list[Finding]:
    normalized = username.strip().lstrip("@")
    return [
        Finding(
            source="X API user lookup",
            category="username_profile",
            status=FindingStatus.skipped,
            confidence=0,
            title="X public profile lookup not enabled",
            url=f"https://x.com/{normalized}" if normalized else None,
            evidence=(
                "X username lookup is wired to this adapter. Enable an approved X API bearer "
                "token through the Vault-backed API settings before live checks."
            ),
            compliance_flags=[ComplianceFlag.public_source, ComplianceFlag.api_terms_required, ComplianceFlag.no_raw_secret, ComplianceFlag.no_bypass],
        )
    ]


async def public_profile_source_lookup(username: str) -> list[Finding]:
    normalized = username.strip().lstrip("@")
    sources = [
        ("GitLab", f"https://gitlab.com/{normalized}"),
        ("Stack Overflow", f"https://stackoverflow.com/users/{normalized}"),
        ("Mastodon", ""),
    ]
    return [
        Finding(
            source=name,
            category="username_profile",
            status=FindingStatus.skipped,
            confidence=0,
            title=f"{name} profile source slot",
            url=url or None,
            evidence="Public profile source adapter is wired. Configure source-specific official APIs or public URL checks before enabling live lookup.",
            compliance_flags=[ComplianceFlag.public_source, ComplianceFlag.no_raw_secret, ComplianceFlag.no_bypass],
        )
        for name, url in sources
    ]
