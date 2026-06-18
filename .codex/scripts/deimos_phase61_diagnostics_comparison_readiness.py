#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT/'.codex/reports/phase61-diagnostics-comparison-readiness.json'

def run(args):
    p = subprocess.run([sys.executable, *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return {"args": args, "returncode": p.returncode, "output_tail": p.stdout[-3000:]}

def main() -> int:
    checks = []
    py_files = [
        'src/update_system.py',
        '.codex/scripts/deimos_staged_update_diagnostics_import.py',
        '.codex/scripts/deimos_staged_update_diagnostics_comparison.py',
        '.codex/scripts/deimos_staged_update_diagnostics_comparison_contract.py',
        '.codex/scripts/deimos_staged_update_diagnostics_comparison_smoke.py',
    ]
    checks.append(run(['-m','py_compile', *py_files]))
    checks.append(run(['.codex/scripts/deimos_staged_update_diagnostics_comparison_contract.py']))
    checks.append(run(['.codex/scripts/deimos_staged_update_diagnostics_comparison_smoke.py']))
    blockers = [c for c in checks if c['returncode'] != 0]
    report = {
        'phase': 61,
        'name': 'diagnostics comparison report',
        'passed': not blockers,
        'blocker_count': len(blockers),
        'checks': checks,
        'locked': {
            'diagnostics_comparison_read_only': True,
            'install_execution_enabled': False,
            'helper_launch_from_gui_enabled': False,
            'non_dry_run_enabled': False,
            'real_install_attempted': False,
        },
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps({'passed': report['passed'], 'blocker_count': len(blockers), 'report': str(REPORT)}, indent=2, sort_keys=True))
    return 0 if report['passed'] else 1
if __name__ == '__main__':
    raise SystemExit(main())
