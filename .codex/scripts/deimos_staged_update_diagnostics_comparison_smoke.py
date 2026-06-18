#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]

def run(args):
    p = subprocess.run([sys.executable, *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return {"args": args, "returncode": p.returncode, "output": p.stdout[-2000:]}

def main() -> int:
    contract = run([".codex/scripts/deimos_staged_update_diagnostics_comparison_contract.py"])
    passed = contract["returncode"] == 0
    print(json.dumps({"passed": passed, "contract": contract}, indent=2, sort_keys=True))
    return 0 if passed else 1
if __name__ == "__main__":
    raise SystemExit(main())
