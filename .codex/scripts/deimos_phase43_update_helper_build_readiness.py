#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path


def call(script: Path, repo: Path, out: Path) -> dict:
    proc = subprocess.run([sys.executable, str(script), str(repo), str(out)], text=True, capture_output=True)
    try:
        data = json.loads(out.read_text(encoding='utf-8'))
    except Exception:
        data = {'ok': False, 'blockers': [proc.stderr or proc.stdout or 'script produced no report']}
    data['exit_code'] = proc.returncode
    return data


def main() -> int:
    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else repo/'.codex/reports/phase43-update-helper-build-readiness.json'
    scripts = repo/'.codex/scripts'
    contract = call(scripts/'deimos_update_helper_build_contract.py', repo, repo/'.codex/reports/phase43-helper-build-contract.json')
    smoke = call(scripts/'deimos_update_helper_build_smoke.py', repo, repo/'.codex/reports/phase43-helper-build-smoke.json')
    blockers = []
    for name, data in [('contract', contract), ('smoke', smoke)]:
        if not data.get('ok'):
            blockers.extend([f'{name}: {b}' for b in data.get('blockers', [])])
    report = {
        'phase': 43,
        'ok': not blockers,
        'helper_build_packaging_scaffold_ready': not blockers,
        'install_still_locked': True,
        'gui_launch_still_locked': True,
        'contract': contract,
        'smoke': smoke,
        'blockers': blockers,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(report, sort_keys=True))
    return 1 if blockers else 0

if __name__ == '__main__':
    raise SystemExit(main())
