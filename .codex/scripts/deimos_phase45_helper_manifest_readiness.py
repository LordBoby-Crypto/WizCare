#!/usr/bin/env python3
"""Aggregate Phase 45 helper release-manifest readiness checks."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

CHECKS=[
    ['.codex/scripts/deimos_release_manifest_helper_integration.py'],
    ['.codex/scripts/deimos_helper_release_asset_matrix.py'],
    ['.codex/scripts/deimos_update_helper_artifact_contract.py'],
]

def run(repo: Path, script: str):
    cmd=[sys.executable, str(repo/script), str(repo), str(repo/'.codex/reports'/ (Path(script).stem + '.json'))]
    proc=subprocess.run(cmd, cwd=repo, text=True, capture_output=True)
    return {'script':script,'returncode':proc.returncode,'stdout':proc.stdout[-2000:],'stderr':proc.stderr[-2000:]}

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('repo', nargs='?', default='.'); p.add_argument('output', nargs='?', default='.codex/reports/phase45-helper-manifest-readiness.json')
    a=p.parse_args(argv); repo=Path(a.repo).resolve(); results=[]; blockers=[]
    for check in CHECKS:
        result=run(repo, check[0]); results.append(result)
        if result['returncode'] != 0: blockers.append(f"{check[0]} failed")
    report={'phase':45,'topic':'helper release-manifest integration','checks':results,'install_execution_locked':True,'gui_launch_locked':True,'blockers':blockers,'passed':not blockers}
    out=Path(a.output); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8'); print(json.dumps(report, sort_keys=True)); return 0 if not blockers else 1
if __name__=='__main__': raise SystemExit(main())
