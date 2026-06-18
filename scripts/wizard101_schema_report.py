#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "wizard101" / "catalog_manifest.json"
SCHEMA_DIR = ROOT / "data" / "wizard101" / "schemas"


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    report = {"schema_version": manifest.get("schema_version"), "checks": [], "blockers": []}
    datasets = manifest.get("datasets") or {}
    for dataset, meta in sorted(datasets.items()):
        path = ROOT / str(meta["path"])
        exists = path.exists()
        has_required_fields = bool(meta.get("required_fields"))
        passed = exists and has_required_fields
        report["checks"].append({"dataset": dataset, "path": str(path), "exists": exists, "has_required_fields": has_required_fields, "passed": passed})
        if not passed:
            report["blockers"].append(f"dataset contract incomplete: {dataset}")
    schema_files = sorted(SCHEMA_DIR.glob("*.json"))
    for schema in schema_files:
        json.loads(schema.read_text(encoding="utf-8"))
    report["schema_files"] = [str(path.relative_to(ROOT)) for path in schema_files]
    report["blockers"].extend([] if schema_files else ["no schema files present"])
    out = ROOT / ".codex" / "reports" / "wizard101-schema-contract.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
