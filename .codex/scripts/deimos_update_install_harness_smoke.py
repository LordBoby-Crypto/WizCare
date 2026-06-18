#!/usr/bin/env python3
"""Run Phase 52 fake updater install harness smoke tests."""
from __future__ import annotations
import importlib.util, json, sys
from pathlib import Path

def load_module(path: Path):
    spec = importlib.util.spec_from_file_location('phase52_harness', path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Cannot load {path}')
    mod = importlib.util.module_from_spec(spec)
    sys.modules['phase52_harness'] = mod
    spec.loader.exec_module(mod)
    return mod

def main() -> int:
    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    path = repo / '.codex/scripts/deimos_update_install_test_harness.py'
    blockers = []
    try:
        mod = load_module(path)
        report = mod.run_all(keep_temp=False)
        if not report.get('passed'):
            blockers.append('harness run_all did not pass')
        if report.get('real_install_attempted'):
            blockers.append('harness reported a real install attempt')
        scenarios = {s['scenario']: s for s in report.get('scenarios', [])}
        for required in ('success','checksum_failure','replacement_failure_with_rollback','exit_code_matrix'):
            if required not in scenarios:
                blockers.append(f'missing scenario result: {required}')
        if scenarios.get('success', {}).get('post_install_verified') is not True:
            blockers.append('success scenario did not verify post-install hash')
        if scenarios.get('checksum_failure', {}).get('checksum_verified') is not False:
            blockers.append('checksum_failure scenario did not fail checksum before replacement')
        if scenarios.get('replacement_failure_with_rollback', {}).get('rollback_used') is not True:
            blockers.append('rollback scenario did not report rollback_used')
    except Exception as exc:
        blockers.append(f'smoke exception: {exc}')
        report = None
    payload = {"phase": 52, "passed": not blockers, "blockers": blockers, "harness_report": report}
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not blockers else 1
if __name__ == '__main__':
    raise SystemExit(main())
