#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.update_system import compare_staged_update_diagnostics_bundles_for_review

def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print("usage: deimos_staged_update_diagnostics_comparison_review.py BEFORE.zip AFTER.zip [REPORT.json]", file=sys.stderr)
        return 2
    report = compare_staged_update_diagnostics_bundles_for_review(argv[1], argv[2])
    out = Path(argv[3]) if len(argv) > 3 else ROOT/'.codex/reports/phase62-diagnostics-comparison-review.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps({"wrote": str(out), "severity": report.get("severity"), "difference_count": report.get("difference_count")}, indent=2, sort_keys=True))
    return 0 if report.get("valid") else 1
if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
