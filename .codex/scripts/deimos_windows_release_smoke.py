#!/usr/bin/env python3
"""Aggregate Windows build/release smoke report for Deimos.
Runs preflight and artifact checks in a conservative, non-mutating mode.
"""
from __future__ import annotations
import importlib.util, json, subprocess, sys
from pathlib import Path


def run_script(script: Path, args: list[str]) -> dict:
    proc = subprocess.run([sys.executable, str(script), *args], text=True, capture_output=True)
    try:
        data = json.loads(proc.stdout or Path(args[-1]).read_text(encoding='utf-8'))
    except Exception:
        data = {'parse_error': True, 'stdout': proc.stdout, 'stderr': proc.stderr}
    data['_returncode'] = proc.returncode
    if proc.stderr:
        data['_stderr'] = proc.stderr
    return data


def main() -> int:
    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    scripts_dir = Path(__file__).resolve().parent
    tmp = repo/'.codex/reports'
    tmp.mkdir(parents=True, exist_ok=True)
    preflight_out = tmp/'phase33-windows-build-preflight.json'
    artifact_out = tmp/'phase33-release-artifact-report.json'
    preflight = run_script(scripts_dir/'deimos_windows_build_preflight.py', [str(repo), str(preflight_out)])
    artifact = run_script(scripts_dir/'deimos_release_artifact_report.py', [str(repo), str(artifact_out)])
    blockers = []
    warnings = []
    for label, data in [('preflight', preflight), ('artifact', artifact)]:
        blockers += [f'{label}: {b}' for b in data.get('blockers', [])]
        warnings += [f'{label}: {w}' for w in data.get('warnings', [])]
    report = {
        'phase': 33,
        'repo': str(repo),
        'preflight': preflight,
        'artifact': artifact,
        'blockers': blockers,
        'warnings': warnings,
        'release_smoke_ready': not blockers,
        'notes': [
            'Missing dist/Deimos.exe is warning-only in pre-build mode.',
            'Run deimos_release_artifact_report.py --require-artifact after a real Windows build.'
        ]
    }
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding='utf-8')
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if blockers else 0

if __name__ == '__main__':
    raise SystemExit(main())
