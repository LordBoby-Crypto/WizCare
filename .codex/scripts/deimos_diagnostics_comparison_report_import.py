#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.update_system import build_diagnostics_comparison_report_import_review  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: deimos_diagnostics_comparison_report_import.py COMPARISON-REPORT.zip", file=sys.stderr)
        return 2
    review = build_diagnostics_comparison_report_import_review(sys.argv[1])
    print(json.dumps(review, indent=2, sort_keys=True))
    return 0 if review.get("valid") and review.get("safe_bundle") else 1


if __name__ == "__main__":
    raise SystemExit(main())
