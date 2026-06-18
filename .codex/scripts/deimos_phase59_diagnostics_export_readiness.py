#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, subprocess, sys

def run(cmd):
    p=subprocess.run(cmd, text=True, capture_output=True)
    return {'cmd':cmd,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}

def main() -> int:
    root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')
    out=Path(sys.argv[2]) if len(sys.argv)>2 else root/'.codex/reports/phase59-diagnostics-export-readiness.json'
    reports=root/'.codex/reports'; reports.mkdir(parents=True, exist_ok=True)
    steps=[]
    py=sys.executable
    for script,name in [
        ('deimos_staged_update_diagnostics_export_contract.py','contract'),
        ('deimos_staged_update_diagnostics_export_smoke.py','smoke'),
    ]:
        steps.append(run([py, str(root/'.codex/scripts'/script), str(root), str(reports/f'phase59-{name}.json')]))
    for path in ['src/update_system.py','src/gui/update_check.py']:
        steps.append(run([py,'-m','py_compile',str(root/path)]))
    blockers=[s for s in steps if s['returncode']!=0]
    out.write_text(json.dumps({'phase':59,'passed':not blockers,'blocker_count':len(blockers),'steps':steps},indent=2), encoding='utf-8')
    return 1 if blockers else 0
if __name__=='__main__':
    raise SystemExit(main())
