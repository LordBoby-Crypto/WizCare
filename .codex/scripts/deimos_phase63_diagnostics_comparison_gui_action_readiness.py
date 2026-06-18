#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def run(args):
    p=subprocess.run([sys.executable,*args], cwd=ROOT, text=True, capture_output=True)
    return {'args':args,'returncode':p.returncode,'stdout':p.stdout[-2500:],'stderr':p.stderr[-2500:]}

def main() -> int:
    scripts=[
        '.codex/scripts/deimos_diagnostics_comparison_gui_action_contract.py',
        '.codex/scripts/deimos_diagnostics_comparison_gui_action_smoke.py',
    ]
    compile_targets=['src/gui/update_check.py','src/update_system.py',*scripts]
    checks=[run(['-m','py_compile',*compile_targets])]
    checks.extend(run([s]) for s in scripts)
    locale_text=(ROOT/'locale/en.lang').read_text(encoding='utf-8')
    keys=[line.split('=',1)[0] for line in locale_text.splitlines() if '=' in line and not line.lstrip().startswith('#')]
    dupes=sorted({k for k in keys if keys.count(k)>1})
    out={
        'phase':63,
        'passed': all(c['returncode']==0 for c in checks) and not dupes,
        'checks': checks,
        'locale_duplicate_keys': dupes,
        'features': {
            'diagnostics_comparison_gui_action_scaffold': True,
            'two_bundle_file_selection': True,
            'read_only_comparison_review': True,
            'executable_payload_import': False,
            'helper_launch_from_gui_enabled': False,
            'install_execution_enabled': False,
            'non_dry_run_enabled': False,
            'real_install_attempted': False,
        },
        'blockers': [],
    }
    if dupes:
        out['blockers'].append('duplicate_locale_keys')
    if not all(c['returncode']==0 for c in checks):
        out['blockers'].append('script_or_compile_failure')
    path=ROOT/'.codex/reports/phase63-diagnostics-comparison-gui-action-readiness.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if out['passed'] else 1
if __name__=='__main__':
    raise SystemExit(main())
