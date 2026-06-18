#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]


def run_script(name: str) -> dict:
    proc = subprocess.run([sys.executable, str(ROOT / '.codex/scripts' / name)], cwd=ROOT, text=True, capture_output=True)
    try:
        payload = json.loads(proc.stdout)
    except Exception:
        payload = {'passed': False, 'stdout': proc.stdout, 'stderr': proc.stderr, 'returncode': proc.returncode}
    payload['returncode'] = proc.returncode
    return payload


def main() -> int:
    contract = run_script('deimos_diagnostics_comparison_gui_wiring_contract.py')
    compile_targets = [
        ROOT / 'src/gui/tab_hotkeys.py',
        ROOT / 'src/gui/update_check.py',
        ROOT / '.codex/scripts/deimos_diagnostics_comparison_gui_wiring_contract.py',
    ]
    compile_results = {}
    for target in compile_targets:
        proc = subprocess.run([sys.executable, '-m', 'py_compile', str(target)], cwd=ROOT, text=True, capture_output=True)
        compile_results[str(target.relative_to(ROOT))] = proc.returncode == 0
    duplicate_locale_keys = {}
    for lang in ['en.lang', 'zh.lang']:
        path = ROOT / 'locale' / lang
        counts = {}
        for line in path.read_text(encoding='utf-8').splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                key = line.split('=', 1)[0].strip()
                counts[key] = counts.get(key, 0) + 1
        duplicate_locale_keys[lang] = sorted(k for k, v in counts.items() if v > 1)
    checks = {
        'contract_passed': contract.get('passed') is True and contract.get('returncode') == 0,
        'compile_passed': all(compile_results.values()),
        'locale_duplicates_absent': all(not v for v in duplicate_locale_keys.values()),
    }
    out = {
        'phase': 64,
        'passed': all(checks.values()),
        'checks': checks,
        'contract': contract,
        'compile_results': compile_results,
        'duplicate_locale_keys': duplicate_locale_keys,
        'read_only': True,
        'install_execution_enabled': False,
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if out['passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
