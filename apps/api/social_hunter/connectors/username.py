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
