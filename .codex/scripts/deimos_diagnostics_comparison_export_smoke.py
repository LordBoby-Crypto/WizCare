#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(script: str) -> dict:
    proc = subprocess.run([sys.executable, str(ROOT / ".codex/scripts" / script)], cwd=ROOT, text=True, capture_output=True)
    return {"script": script, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr, "passed": proc.returncode == 0}


def main() -> int:
    checks = [run("deimos_diagnostics_comparison_export_contract.py")]
    result = {"phase": 65, "checks": checks, "passed": all(c["passed"] for c in checks)}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
