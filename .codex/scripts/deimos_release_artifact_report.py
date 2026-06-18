#!/usr/bin/env python3
"""Report Deimos release artifact presence, size, and SHA256.
Can be run before or after a build. Missing dist artifact is a blocker only with --require-artifact.
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('repo', nargs='?', default='.')
    p.add_argument('out', nargs='?')
    p.add_argument('--require-artifact', action='store_true')
    args = p.parse_args()
    repo = Path(args.repo)
    exe = repo/'dist/Deimos.exe'
    sha_file = repo/'dist/Deimos.exe.sha256'
    blockers, warnings = [], []
    artifact = {'path': 'dist/Deimos.exe', 'exists': exe.exists()}
    if exe.exists():
        digest = sha256(exe)
        artifact.update({'size_bytes': exe.stat().st_size, 'sha256': digest})
        if exe.stat().st_size < 5_000_000:
            warnings.append('dist/Deimos.exe is smaller than expected for a bundled GUI executable')
        if sha_file.exists():
            txt = sha_file.read_text(encoding='utf-8', errors='ignore').strip()
            artifact['sha256_file_exists'] = True
            artifact['sha256_file_text'] = txt
            artifact['sha256_file_matches'] = digest in txt
            if digest not in txt:
                blockers.append('dist/Deimos.exe.sha256 does not match dist/Deimos.exe')
        else:
            artifact['sha256_file_exists'] = False
            warnings.append('dist/Deimos.exe.sha256 is missing; release workflow should create it')
    elif args.require_artifact:
        blockers.append('dist/Deimos.exe is missing')
    else:
        warnings.append('dist/Deimos.exe not present; run after build for artifact hash validation')
    report = {
        'phase': 33,
        'repo': str(repo),
        'artifact': artifact,
        'require_artifact': args.require_artifact,
        'blockers': blockers,
        'warnings': warnings,
        'artifact_report_ready': not blockers,
    }
    if args.out:
        out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding='utf-8')
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if blockers else 0

if __name__ == '__main__':
    raise SystemExit(main())
