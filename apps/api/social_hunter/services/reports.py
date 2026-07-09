from datetime import datetime, timezone

from social_hunter.models import Finding, SearchResponse, TargetType


def render_markdown_report(search: SearchResponse) -> str:
    lines = [
        "# Social Hunter Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Target type: {_target_type(search.target_type)}",
        f"Target: {search.target}",
        f"Status: {search.status}",
        "",
        "## Findings",
    ]
    for finding in search.findings:
        lines.extend(_finding_lines(finding))
    return "\n".join(lines) + "\n"


def _target_type(target_type: TargetType | str) -> str:
    return target_type.value if isinstance(target_type, TargetType) else target_type


def _finding_lines(finding: Finding) -> list[str]:
    url = str(finding.url) if finding.url else "n/a"
    flags = ", ".join(flag.value for flag in finding.compliance_flags)
    return [
        "",
        f"### {finding.source}",
        f"- Category: {finding.category}",
        f"- Status: {finding.status.value}",
        f"- Confidence: {finding.confidence:.2f}",
        f"- URL: {url}",
        f"- Evidence: {finding.evidence}",
        f"- Flags: {flags}",
    ]
