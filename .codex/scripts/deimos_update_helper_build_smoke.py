#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def main() -> int:
    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else repo/'.codex/reports/phase43-helper-build-smoke.json'
    helper_dir = repo/'libs/updater_helper'
    blockers: list[str] = []
    checks = {}
    for rel in ['deimos_updater_helper.py', 'build_helper.py']:
        proc = run([sys.executable, '-m', 'py_compile', str(helper_dir/rel)])
        checks[f'compile_{rel}'] = proc.returncode == 0
        if proc.returncode != 0:
            blockers.append(f'{rel} failed py_compile: {proc.stderr}')
    proc = run([sys.executable, str(helper_dir/'build_helper.py'), '--report', str(repo/'.codex/reports/phase43-build-helper-self-report.json')], cwd=str(helper_dir))
    checks['build_helper_preflight_runs'] = proc.returncode == 0
    if proc.returncode != 0:
        blockers.append('build_helper.py preflight failed: ' + (proc.stderr or proc.stdout))
    report = {'phase': 43, 'ok': not blockers, 'checks': checks, 'blockers': blockers}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(report, sort_keys=True))
    return 1 if blockers else 0

if __name__ == '__main__':
    raise SystemExit(main())
