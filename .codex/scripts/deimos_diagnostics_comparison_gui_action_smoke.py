#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def run(args):
    p=subprocess.run([sys.executable,*args], cwd=ROOT, text=True, capture_output=True)
    return {'args':args,'returncode':p.returncode,'stdout':p.stdout[-2000:],'stderr':p.stderr[-2000:]}

def main() -> int:
    contract=run(['.codex/scripts/deimos_diagnostics_comparison_gui_action_contract.py'])
    compile_gui=run(['-m','py_compile','src/gui/update_check.py','src/update_system.py'])
    passed=contract['returncode']==0 and compile_gui['returncode']==0
    out={'phase':63,'passed':passed,'contract':contract,'compile':compile_gui,'review_only':True,'install_execution_enabled':False,'real_install_attempted':False}
    path=ROOT/'.codex/reports/phase63-diagnostics-comparison-gui-action-smoke.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if passed else 1
if __name__=='__main__':
    raise SystemExit(main())
