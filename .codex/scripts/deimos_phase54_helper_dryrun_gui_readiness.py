#!/usr/bin/env python3
from pathlib import Path
import json, subprocess, sys

def run(cmd):
    p=subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return {'cmd':cmd,'returncode':p.returncode,'output':p.stdout}

def main():
    root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')
    out=Path(sys.argv[2]) if len(sys.argv)>2 else root/'.codex/reports/phase54-helper-dryrun-gui-readiness.json'
    reports=[]
    py=sys.executable
    checks=[
        [py, str(root/'.codex/scripts/deimos_helper_dryrun_gui_contract.py'), str(root), str(root/'.codex/reports/phase54-contract.json')],
        [py, str(root/'.codex/scripts/deimos_helper_dryrun_gui_smoke.py'), str(root), str(root/'.codex/reports/phase54-smoke.json')],
        [py, '-m', 'py_compile', str(root/'src/update_system.py'), str(root/'src/gui/update_check.py')],
    ]
    blockers=[]
    for cmd in checks:
        r=run(cmd); reports.append(r)
        if r['returncode']!=0: blockers.append('failed: '+' '.join(cmd))
    result={'passed': not blockers, 'phase':54, 'blockers':blockers, 'reports':reports, 'locks': {'helper_launch_enabled': False, 'install_execution_enabled': False, 'non_dry_run_enabled': False}}
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 0 if not blockers else 1
if __name__ == '__main__': raise SystemExit(main())
