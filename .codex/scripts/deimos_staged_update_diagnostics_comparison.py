#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.update_system import compare_staged_update_diagnostics_bundles

def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print("usage: deimos_staged_update_diagnostics_comparison.py LEFT.zip RIGHT.zip [REPORT.json]", file=sys.stderr)
        return 2
    report = compare_staged_update_diagnostics_bundles(argv[1], argv[2])
    if len(argv) > 3:
        Path(argv[3]).parent.mkdir(parents=True, exist_ok=True)
        Path(argv[3]).write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps({"valid": report.get("valid"), "headline": report.get("headline"), "difference_count": report.get("difference_count"), "changed_fields": report.get("changed_fields", []), "blocker_count": report.get("blocker_count", 0)}, indent=2, sort_keys=True))
    return 0 if report.get("valid") and report.get("blocker_count", 0) == 0 else 1
if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
