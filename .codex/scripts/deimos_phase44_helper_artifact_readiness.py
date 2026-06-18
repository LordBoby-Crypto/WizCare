#!/usr/bin/env python3
"""Aggregate Phase 44 helper executable artifact readiness checks."""
from __future__ import annotations
import argparse, importlib.util, json, subprocess, sys
from pathlib import Path

SCRIPTS = [
    ("artifact_contract", "deimos_update_helper_artifact_contract.py"),
    ("artifact_report", "deimos_update_helper_artifact_report.py"),
    ("manifest_inclusion", "deimos_update_helper_manifest_inclusion.py"),
]

def run(repo: Path, name: str, script: str, require_artifact: bool) -> dict:
    out = repo / ".codex" / "reports" / f"phase44-{name}.json"
    cmd = [sys.executable, str(repo / ".codex" / "scripts" / script), str(repo), str(out)]
    if require_artifact and name in {"artifact_contract", "artifact_report"}:
        cmd.append("--require-artifact")
    proc = subprocess.run(cmd, text=True, capture_output=True)
    try: data=json.loads(out.read_text(encoding='utf-8'))
    except Exception: data={"blockers":["could not read subreport"],"warnings":[],"passed":False}
    data["exit_code"] = proc.returncode
    data["stderr"] = proc.stderr[-1000:]
    return data

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("repo", nargs="?", default="."); p.add_argument("output", nargs="?", default=".codex/reports/phase44-helper-artifact-readiness.json"); p.add_argument("--require-artifact", action="store_true")
    a=p.parse_args(argv); repo=Path(a.repo).resolve(); reports={name:run(repo,name,script,a.require_artifact) for name,script in SCRIPTS}; blockers=[]; warnings=[]
    for name,r in reports.items():
        blockers += [f"{name}: {b}" for b in r.get('blockers', [])]
        warnings += [f"{name}: {w}" for w in r.get('warnings', [])]
        if r.get('exit_code') not in (0, None) and r.get('blockers'):
            pass
    result={"phase":44,"checks":reports,"install_locked":True,"gui_launch_locked":True,"non_dry_run_locked":True,"blockers":blockers,"warnings":warnings,"passed":not blockers}
    out=Path(a.output); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding='utf-8'); print(json.dumps(result, sort_keys=True)); return 0 if result['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
