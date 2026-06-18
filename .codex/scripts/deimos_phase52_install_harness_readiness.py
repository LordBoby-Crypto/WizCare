#!/usr/bin/env python3
"""Aggregate Phase 52 updater install harness readiness."""
from __future__ import annotations
import json, py_compile, subprocess, sys
from pathlib import Path

def run(cmd):
    p = subprocess.run(cmd, text=True, capture_output=True)
    try:
        data = json.loads(p.stdout or '{}')
    except Exception:
        data = {"raw_stdout": p.stdout, "raw_stderr": p.stderr}
    return {"cmd": cmd, "returncode": p.returncode, "data": data, "stderr": p.stderr}

def main() -> int:
    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else repo/'.codex/reports/phase52-install-harness-readiness.json'
    scripts = [
        repo/'.codex/scripts/deimos_update_install_test_harness.py',
        repo/'.codex/scripts/deimos_update_install_harness_contract.py',
        repo/'.codex/scripts/deimos_update_install_harness_smoke.py',
    ]
    blockers = []
    for script in scripts:
        try:
            py_compile.compile(str(script), doraise=True)
        except Exception as exc:
            blockers.append(f'compile failed for {script.name}: {exc}')
    reports = []
    if not blockers:
        reports.append(run([sys.executable, str(repo/'.codex/scripts/deimos_update_install_harness_contract.py'), str(repo)]))
        reports.append(run([sys.executable, str(repo/'.codex/scripts/deimos_update_install_harness_smoke.py'), str(repo)]))
        for r in reports:
            if r['returncode'] != 0 or not r['data'].get('passed'):
                blockers.append(f"check failed: {' '.join(r['cmd'])}")
    payload = {"phase": 52, "passed": not blockers, "blockers": blockers, "reports": reports, "install_execution_enabled": False, "helper_launch_enabled": False}
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not blockers else 1
if __name__ == '__main__':
    raise SystemExit(main())
