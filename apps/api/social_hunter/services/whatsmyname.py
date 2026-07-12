from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from social_hunter.connectors.username import DATA_PATH

WHATSMyNAME_URL = "https://raw.githubusercontent.com/WebBreacher/WhatsMyName/main/wmn-data.json"


def _source_from_site(site: dict[str, Any]) -> dict[str, Any] | None:
    name = str(site.get("name", "")).strip()
    uri = str(site.get("uri_check") or site.get("uri_pretty") or "").strip()
    if not name or "{account}" not in uri:
        return None
    return {
        "name": name,
        "category": str(site.get("cat", "other") or "other"),
        "url": uri,
        "demo_found_for": site.get("known", [])[:5] if isinstance(site.get("known"), list) else [],
        "imported_from": "WhatsMyName",
    }


def import_whatsmyname_payload(payload: dict[str, Any], limit: int | None = None, dry_run: bool = True) -> dict[str, Any]:
    sites = payload.get("sites", [])
    if limit:
        sites = sites[:limit]
    sources = [_source_from_site(site) for site in sites]
    normalized = [source for source in sources if source]
    result = {
        "loaded": len(sites),
        "importable": len(normalized),
        "dry_run": dry_run,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if dry_run:
        return result
    current = {"username_sources": []}
    if DATA_PATH.exists():
        import json
        current = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    by_name = {source["name"]: source for source in current.get("username_sources", [])}
    for source in normalized:
        by_name[source["name"]] = source
    updated = {"username_sources": sorted(by_name.values(), key=lambda item: item["name"].lower())}
    import json
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(updated, indent=2), encoding="utf-8")
    result["stored_total"] = len(updated["username_sources"])
    return result


async def fetch_whatsmyname(limit: int | None = None, dry_run: bool = True) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(WHATSMyNAME_URL)
        response.raise_for_status()
        return import_whatsmyname_payload(response.json(), limit=limit, dry_run=dry_run)


def local_whatsmyname_status() -> dict[str, Any]:
    import json
    if not DATA_PATH.exists():
        return {"stored_total": 0, "path": str(DATA_PATH)}
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    sources = data.get("username_sources", [])
    imported = [source for source in sources if source.get("imported_from") == "WhatsMyName"]
    return {"stored_total": len(sources), "whatsmyname_total": len(imported), "path": str(DATA_PATH)}
