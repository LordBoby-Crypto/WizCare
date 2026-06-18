#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / '.codex/reports/phase64-diagnostics-comparison-gui-wiring-readiness.json'


def run(name: str) -> dict:
    proc = subprocess.run([sys.executable, str(ROOT / '.codex/scripts' / name)], cwd=ROOT, text=True, capture_output=True)
    try:
        payload = json.loads(proc.stdout)
    except Exception:
        payload = {'passed': False, 'stdout': proc.stdout, 'stderr': proc.stderr}
    payload['returncode'] = proc.returncode
    return payload


def main() -> int:
    scripts = [
        'deimos_diagnostics_comparison_gui_action_contract.py',
        'deimos_diagnostics_comparison_gui_wiring_contract.py',
        'deimos_diagnostics_comparison_gui_wiring_smoke.py',
    ]
    results = {name: run(name) for name in scripts}
    compile_targets = [
        ROOT / 'src/gui/tab_hotkeys.py',
        ROOT / 'src/gui/update_check.py',
        ROOT / '.codex/scripts/deimos_diagnostics_comparison_gui_wiring_contract.py',
        ROOT / '.codex/scripts/deimos_diagnostics_comparison_gui_wiring_smoke.py',
    ]
    compile_results = {}
    for target in compile_targets:
        proc = subprocess.run([sys.executable, '-m', 'py_compile', str(target)], cwd=ROOT, text=True, capture_output=True)
        compile_results[str(target.relative_to(ROOT))] = {'passed': proc.returncode == 0, 'stderr': proc.stderr}
    blockers = []
    for name, result in results.items():
        if result.get('returncode') != 0 or result.get('passed') is not True:
            blockers.append(f'{name} failed')
    for name, result in compile_results.items():
        if not result['passed']:
            blockers.append(f'{name} did not compile')
    out = {
        'phase': 64,
        'name': 'diagnostics comparison GUI menu/button wiring',
        'passed': not blockers,
        'blockers': blockers,
        'results': results,
        'compile_results': compile_results,
        'diagnostics_comparison_button_wired': True,
        'diagnostics_comparison_read_only': True,
        'executable_payload_import': False,
        'helper_launch_from_gui_enabled': False,
        'install_execution_enabled': False,
        'non_dry_run_enabled': False,
        'real_install_attempted': False,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(out, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if out['passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
