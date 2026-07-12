import json
from pathlib import Path

from social_hunter.models import ComplianceFlag, Finding, FindingStatus

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "sources.json"


async def username_lookup(username: str) -> list[Finding]:
    sources = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    normalized = username.strip().lstrip("@")
    findings: list[Finding] = []

    for source in sources["username_sources"]:
        profile_url = source["url"].replace("{account}", normalized)
        simulated_found = normalized.lower() in source.get("demo_found_for", [])
        findings.append(
            Finding(
                source=source["name"],
                category=source["category"],
                status=FindingStatus.found if simulated_found else FindingStatus.unknown,
                confidence=0.86 if simulated_found else 0.35,
                title=f"{source['name']} profile check",
                url=profile_url,
                evidence=(
                    "Demo fixture indicates a likely public profile."
                    if simulated_found
                    else "Connector stub generated the public profile URL; live HTTP check is not enabled yet."
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
    return [
        Finding(
            source="GitHub REST Users API",
            category="username_profile",
            status=FindingStatus.skipped,
            confidence=0,
            title="GitHub public profile lookup not enabled",
            url=f"https://github.com/{normalized}" if normalized else None,
            evidence=(
                "GitHub public profile lookup is wired to this adapter. Enable a Vault-backed "
                "token reference when higher API limits or live metadata are required."
            ),
            compliance_flags=[
                ComplianceFlag.public_source,
                ComplianceFlag.api_terms_required,
                ComplianceFlag.no_raw_secret,
                ComplianceFlag.no_bypass,
            ],
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
            compliance_flags=[
                ComplianceFlag.public_source,
                ComplianceFlag.api_terms_required,
                ComplianceFlag.no_raw_secret,
                ComplianceFlag.no_bypass,
            ],
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
            compliance_flags=[
                ComplianceFlag.public_source,
                ComplianceFlag.api_terms_required,
                ComplianceFlag.no_raw_secret,
                ComplianceFlag.no_bypass,
            ],
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
            evidence=(
                "Public profile source adapter is wired. Configure source-specific official "
                "APIs or public URL checks before enabling live lookup."
            ),
            compliance_flags=[
                ComplianceFlag.public_source,
                ComplianceFlag.no_raw_secret,
                ComplianceFlag.no_bypass,
            ],
        )
        for name, url in sources
    ]
