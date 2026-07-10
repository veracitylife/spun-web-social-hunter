#!/usr/bin/env python3
"""Import WhatsMyName dataset into Social Hunter."""
import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
from sqlalchemy import create_engine, insert
from sqlalchemy.orm import sessionmaker

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from social_hunter.db import DATABASE_URL, SourceCapabilityRecord


WHATSMyNAME_URL = "https://raw.githubusercontent.com/WebBreacher/WhatsMyName/main/wmn-data.json"


def fetch_whatsmyname_data(url: str = WHATSMyNAME_URL) -> dict[str, Any]:
    """Fetch WhatsMyName dataset from GitHub."""
    print(f"Fetching WhatsMyName data from {url}...")

    response = httpx.get(url, timeout=60)
    response.raise_for_status()

    return response.json()


def transform_to_capability(site: dict) -> dict[str, Any]:
    """Transform WhatsMyName site to Social Hunter capability."""
    # Map WhatsMyName categories to Social Hunter categories
    category_map = {
        "social": "social",
        "gaming": "gaming",
        "music": "entertainment",
        "adult": "adult",
        "coding": "development",
        "finance": "finance",
        "dating": "dating",
        "blogging": "blogging",
        "shopping": "shopping",
        "tech": "technology",
        "forums": "forum",
        "images": "images",
        "news": "news",
        "porn": "adult",
        "art": "art",
        "business": "business",
        "education": "education",
        "health": "health",
        "travel": "travel",
        "video": "video",
        "wiki": "wiki",
        "other": "other",
    }

    raw_category = site.get("cat", "other").lower()
    category = category_map.get(raw_category, "other")

    # Build capability record
    return {
        "id": str(uuid4()),
        "source_id": f"wmn_{site['name'].lower().replace(' ', '_')}",
        "name": site["name"],
        "category": category,
        "target_types": ["username"],  # WhatsMyName is username-focused
        "status": "stubbed",  # Start as stubbed, enable after testing
        "terms_note": f"WhatsMyName dataset. URI: {site.get('uri_check', '')}",
        "data_returned": json.dumps([
            "profile_url",
            "username",
            "exists",
            "response_code",
        ]),
        "raw_payload_storage_allowed": False,
        "config": json.dumps({
            "uri_check": site.get("uri_check", ""),
            "uri_pretty": site.get("uri_pretty", ""),
            "e_code": site.get("e_code"),
            "e_string": site.get("e_string"),
            "m_string": site.get("m_string"),
            "m_code": site.get("m_code"),
            "known_accounts": site.get("known", []),
        }),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


async def import_to_database(
    sites: list[dict],
    dry_run: bool = True,
    db_url: str = DATABASE_URL,
) -> tuple[int, int]:
    """Import sites to database."""
    engine = create_engine(db_url.replace("postgresql+asyncpg://", "postgresql://"))
    Session = sessionmaker(bind=engine)
    session = Session()

    created = 0
    skipped = 0

    try:
        for site in sites:
            source_id = f"wmn_{site['name'].lower().replace(' ', '_')}"

            # Check if already exists
            existing = session.query(SourceCapabilityRecord).filter_by(
                source_id=source_id
            ).first()

            if existing:
                print(f"  Skipping existing: {site['name']}")
                skipped += 1
                continue

            # Transform and insert
            capability = transform_to_capability(site)
            stmt = insert(SourceCapabilityRecord).values(**capability)
            session.execute(stmt)
            created += 1

            if created % 100 == 0:
                print(f"  Processed {created} new sources...")

        if not dry_run:
            session.commit()
            print(f"\nCommitted {created} new sources to database")
        else:
            session.rollback()
            print(f"\nDRY RUN: Would have created {created} sources")

        return created, skipped

    except Exception as exc:
        session.rollback()
        raise exc
    finally:
        session.close()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Import WhatsMyName dataset into Social Hunter"
    )
    parser.add_argument(
        "--file",
        "-f",
        help="Local JSON file instead of fetching from GitHub",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show what would be imported without committing",
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        help="Limit number of sites to import",
    )

    args = parser.parse_args()

    # Load data
    if args.file:
        print(f"Loading from {args.file}...")
        with open(args.file) as f:
            data = json.load(f)
    else:
        data = fetch_whatsmyname_data()

    sites = data.get("sites", [])
    print(f"Loaded {len(sites)} sites from WhatsMyName dataset")

    if args.limit:
        sites = sites[:args.limit]
        print(f"Limited to first {args.limit} sites")

    # Import
    created, skipped = asyncio.run(import_to_database(sites, dry_run=args.dry_run))

    print(f"\nImport complete:")
    print(f"  Created: {created}")
    print(f"  Skipped (existing): {skipped}")
    print(f"  Total processed: {created + skipped}")


if __name__ == "__main__":
    main()
