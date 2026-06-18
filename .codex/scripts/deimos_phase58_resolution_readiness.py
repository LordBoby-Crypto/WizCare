#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]

def run(script: str, out: Path) -> dict:
    proc = subprocess.run([sys.executable, str(ROOT/'.codex/scripts'/script), str(out)], cwd=ROOT, text=True, capture_output=True)
    try:
        data = json.loads(out.read_text(encoding='utf-8'))
    except Exception:
        data = {'ok': False, 'blockers': ['could not parse output'], 'stdout': proc.stdout, 'stderr': proc.stderr}
    data['returncode'] = proc.returncode
    if proc.returncode != 0:
        data['ok'] = False
    return data

def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT/'.codex/reports/phase58-resolution-readiness.json'
    reports = ROOT/'.codex/reports'; reports.mkdir(parents=True, exist_ok=True)
    checks = {
        'contract': run('deimos_staged_update_resolution_guidance_contract.py', reports/'phase58-resolution-contract.json'),
        'smoke': run('deimos_staged_update_resolution_guidance_smoke.py', reports/'phase58-resolution-smoke.json'),
    }
    blockers = []
    for name, result in checks.items():
        if not result.get('ok'):
            blockers.append(name)
    report = {'ok': not blockers, 'blockers': blockers, 'checks': checks, 'install_execution_enabled': False, 'helper_launch_from_gui_enabled': False}
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report['ok'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
