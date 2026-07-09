import json
from pathlib import Path


def normalize_whatsmyname(input_path: Path, output_path: Path) -> None:
    data = json.loads(input_path.read_text(encoding="utf-8"))
    sites = data.get("sites", data if isinstance(data, list) else [])
    normalized = {"username_sources": []}
    for site in sites:
        name = site.get("name") or site.get("site")
        url = site.get("uri_check") or site.get("url") or site.get("urlMain")
        if not name or not url or "{account}" not in url:
            continue
        normalized["username_sources"].append({
            "name": name,
            "category": site.get("cat", "username"),
            "url": url,
            "demo_found_for": [],
        })
    output_path.write_text(json.dumps(normalized, indent=2), encoding="utf-8")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Normalize a WhatsMyName-style JSON file for Social Hunter.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    normalize_whatsmyname(args.input, args.output)
