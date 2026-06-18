#!/usr/bin/env python3
"""Aggregate Phase 47 helper post-build readiness checks."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

CHECKS = [
    ('helper_postbuild_enforcement', ['.codex/scripts/deimos_helper_postbuild_enforcement.py', '.', '.codex/reports/phase47-helper-postbuild-enforcement.json']),
    ('helper_artifact_contract', ['.codex/scripts/deimos_update_helper_artifact_contract.py', '.', '.codex/reports/phase47-helper-artifact-contract.json']),
    ('helper_manifest_integration', ['.codex/scripts/deimos_release_manifest_helper_integration.py', '.', '.codex/reports/phase47-helper-manifest-integration.json']),
    ('helper_release_asset_matrix', ['.codex/scripts/deimos_helper_release_asset_matrix.py', '.', '.codex/reports/phase47-helper-asset-matrix.json']),
]


def run(repo: Path) -> dict:
    checks = []
    blockers = []
    warnings = []
    for name, cmd in CHECKS:
        proc = subprocess.run([sys.executable, *cmd], cwd=repo, text=True, capture_output=True)
        checks.append({
            'name': name,
            'returncode': proc.returncode,
            'stdout': proc.stdout[-4000:],
            'stderr': proc.stderr[-4000:],
        })
        if proc.returncode != 0:
            blockers.append(f'{name} failed')
        try:
            data = json.loads(proc.stdout.strip().splitlines()[-1]) if proc.stdout.strip() else {}
            warnings.extend([f'{name}: {w}' for w in data.get('warnings', [])])
        except Exception:
            pass
    return {
        'phase': 47,
        'purpose': 'helper artifact post-build readiness',
        'install_execution_locked': True,
        'checks': checks,
        'warnings': warnings,
        'blockers': blockers,
        'passed': not blockers,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument('repo', nargs='?', default='.')
    p.add_argument('output', nargs='?', default='.codex/reports/phase47-helper-postbuild-readiness.json')
    a = p.parse_args(argv)
    repo = Path(a.repo).resolve()
    result = run(repo)
    out = repo / a.output if not Path(a.output).is_absolute() else Path(a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(result, sort_keys=True))
    return 0 if result['passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
