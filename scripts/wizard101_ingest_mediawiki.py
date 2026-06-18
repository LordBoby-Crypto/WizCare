#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SOURCE_CATALOG = ROOT / "data" / "wizard101" / "source_catalog.json"
RAW_DIR = ROOT / "data" / "wizard101" / "raw" / "wizard101central-wiki"


def build_categorymembers_url(api_url: str, title: str, limit: int, cmcontinue: str | None = None) -> str:
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": title,
        "cmlimit": str(limit),
        "format": "json",
    }
    if cmcontinue:
        params["cmcontinue"] = cmcontinue
    return f"{api_url}?{urlencode(params)}"


def fetch_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": "Deimos-WizCare-knowledge-ingest/1.0"})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def category_member_records(api_url: str, title: str, group: str, limit: int, pages: int) -> list[dict]:
    records: list[dict] = []
    cmcontinue = None
    retrieved_at = datetime.now(timezone.utc).isoformat()
    for _ in range(max(pages, 1)):
        url = build_categorymembers_url(api_url, title, limit, cmcontinue)
        payload = fetch_json(url)
        for member in payload.get("query", {}).get("categorymembers", []):
            records.append({
                "source_id": "wizard101central-wiki",
                "source_category": title,
                "group": group,
                "pageid": member.get("pageid"),
                "ns": member.get("ns"),
                "title": member.get("title"),
                "retrieved_at": retrieved_at,
                "source_api_url": url,
                "verification": {"level": "source-linked"},
            })
        cmcontinue = payload.get("continue", {}).get("cmcontinue")
        if not cmcontinue:
            break
    return records


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest Wizard101 Central Wiki category member stubs as raw source-linked records.")
    parser.add_argument("--group", choices=["gear", "enemies", "spells", "quests", "worlds"], required=True)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true", help="Build the ingestion plan without network calls or writes.")
    args = parser.parse_args()

    source_catalog = json.loads(SOURCE_CATALOG.read_text(encoding="utf-8"))
    wiki = next(source for source in source_catalog["primary_sources"] if source["id"] == "wizard101central-wiki")
    categories = source_catalog["category_seed_queries"].get(args.group, [])
    report = {
        "group": args.group,
        "dry_run": args.dry_run,
        "categories": categories,
        "written_files": [],
        "record_count": 0,
        "blockers": [],
    }
    if args.dry_run:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    for category in categories:
        records = category_member_records(wiki["mediawiki_api"], category, args.group, args.limit, args.pages)
        safe_name = category.replace("Category:", "").replace(" ", "_").replace("/", "_").lower()
        out = RAW_DIR / args.group / f"{safe_name}.jsonl"
        write_jsonl(out, records)
        report["written_files"].append(str(out.relative_to(ROOT)))
        report["record_count"] += len(records)
    out_report = ROOT / ".codex" / "reports" / f"wizard101-raw-{args.group}-ingest.json"
    out_report.parent.mkdir(parents=True, exist_ok=True)
    out_report.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
