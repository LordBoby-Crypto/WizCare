#!/usr/bin/env python3
"""Aggregate Phase 46 helper release workflow readiness checks."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

CHECKS = [
    ("helper_workflow_integration", [".codex/scripts/deimos_helper_release_workflow_integration.py", ".", ".codex/reports/phase46-helper-workflow-integration.json"]),
    ("helper_artifact_contract", [".codex/scripts/deimos_update_helper_artifact_contract.py", ".", ".codex/reports/phase46-helper-artifact-contract.json"]),
    ("helper_manifest_integration", [".codex/scripts/deimos_release_manifest_helper_integration.py", ".", ".codex/reports/phase46-helper-manifest-integration.json"]),
]

def run(repo: Path) -> dict:
    checks=[]; blockers=[]
    for name, cmd in CHECKS:
        proc = subprocess.run([sys.executable, *cmd], cwd=repo, text=True, capture_output=True)
        checks.append({"name": name, "returncode": proc.returncode, "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-4000:]})
        if proc.returncode != 0:
            blockers.append(f"{name} failed")
    return {"phase":46,"purpose":"helper release workflow readiness","install_locked":True,"checks":checks,"blockers":blockers,"passed":not blockers}

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("repo", nargs="?", default="."); p.add_argument("output", nargs="?", default=".codex/reports/phase46-helper-workflow-readiness.json")
    a=p.parse_args(argv); repo=Path(a.repo).resolve(); res=run(repo); out=Path(a.output); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(res,indent=2,sort_keys=True), encoding='utf-8'); print(json.dumps(res, sort_keys=True)); return 0 if res['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
