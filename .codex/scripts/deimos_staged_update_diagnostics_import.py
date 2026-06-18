#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.update_system import import_staged_update_diagnostics_bundle

def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: deimos_staged_update_diagnostics_import.py BUNDLE.zip [REPORT.json]", file=sys.stderr)
        return 2
    report = import_staged_update_diagnostics_bundle(argv[1])
    if len(argv) > 2:
        Path(argv[2]).parent.mkdir(parents=True, exist_ok=True)
        Path(argv[2]).write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps({"valid": report.get("valid"), "safe_bundle": report.get("safe_bundle"), "errors": report.get("errors", []), "summary": report.get("summary", {})}, indent=2, sort_keys=True))
    return 0 if report.get("valid") else 1
if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
