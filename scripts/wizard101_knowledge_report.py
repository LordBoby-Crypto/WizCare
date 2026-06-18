#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.wizard101_knowledge import load_default_catalog


def main() -> int:
    catalog = load_default_catalog()
    report = catalog.coverage_report()
    out = ROOT / ".codex" / "reports" / "wizard101-knowledge-coverage.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
