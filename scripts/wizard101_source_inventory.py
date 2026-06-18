#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen, Request

ROOT = Path(__file__).resolve().parents[1]
SOURCE_CATALOG = ROOT / "data" / "wizard101" / "source_catalog.json"


def fetch_category_count(api_url: str, title: str, limit: int) -> dict:
    params = urlencode({
        "action": "query",
        "list": "categorymembers",
        "cmtitle": title,
        "cmlimit": str(limit),
        "format": "json",
    })
    request = Request(f"{api_url}?{params}", headers={"User-Agent": "Deimos-WizCare-knowledge-audit/1.0"})
    with urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    members = data.get("query", {}).get("categorymembers", [])
    return {"title": title, "sample_count": len(members), "sample_titles": [m.get("title") for m in members[:10]]}


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit configured Wizard101 source categories for future full-game ingestion.")
    parser.add_argument("--online", action="store_true", help="Query configured MediaWiki APIs for sample category counts.")
    parser.add_argument("--limit", type=int, default=10, help="Per-category sample limit for online checks.")
    args = parser.parse_args()

    catalog = json.loads(SOURCE_CATALOG.read_text(encoding="utf-8"))
    report = {
        "schema_version": catalog.get("schema_version"),
        "online": args.online,
        "source_count": len(catalog.get("primary_sources") or []),
        "category_groups": sorted((catalog.get("category_seed_queries") or {}).keys()),
        "checks": [],
        "blockers": [],
    }
    wiki = next((source for source in catalog.get("primary_sources", []) if source.get("mediawiki_api")), None)
    if not wiki:
        report["blockers"].append("no MediaWiki source configured")
    if args.online and wiki:
        api_url = wiki["mediawiki_api"]
        for group, titles in sorted((catalog.get("category_seed_queries") or {}).items()):
            for title in titles:
                result = fetch_category_count(api_url, title, args.limit)
                result["group"] = group
                report["checks"].append(result)
    out = ROOT / ".codex" / "reports" / "wizard101-source-inventory.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
