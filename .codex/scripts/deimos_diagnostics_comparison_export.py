#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.update_system import export_diagnostics_comparison_report_bundle  # noqa: E402


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: deimos_diagnostics_comparison_export.py BEFORE.zip AFTER.zip OUTPUT.zip", file=sys.stderr)
        return 2
    report = export_diagnostics_comparison_report_bundle(sys.argv[1], sys.argv[2], sys.argv[3])
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("safe_bundle") else 1


if __name__ == "__main__":
    raise SystemExit(main())
