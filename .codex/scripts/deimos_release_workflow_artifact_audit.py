#!/usr/bin/env python3
"""Audit GitHub workflows for Deimos release artifact hardening."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

REQUIRED_PATTERNS = {
    'uses_deimos_spec': r'Deimos\.spec',
    'generates_sha256': r'Deimos\.exe\.sha256|sha256sum\s+dist/Deimos\.exe|Get-FileHash.*Deimos\.exe',
    'references_release_manifest': r'release-manifest\.json',
    'release_uploads_exe': r'dist/Deimos\.exe',
    'release_uploads_sha': r'dist/Deimos\.exe\.sha256',
}
RELEASE_WORKFLOWS = {'build.yml', 'release.yml'}
BUILD_WORKFLOWS = {'ci.yml', 'develop.yml', 'build.yml', 'release.yml'}

def audit_file(path: Path) -> dict:
    text = path.read_text(encoding='utf-8', errors='ignore')
    checks = {k: bool(re.search(v, text, re.I | re.S)) for k, v in REQUIRED_PATTERNS.items()}
    if path.name not in RELEASE_WORKFLOWS:
        checks['release_uploads_exe'] = True
        checks['release_uploads_sha'] = True
    return {'workflow': path.name, 'checks': checks, 'passed': all(checks.values())}

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('repo', nargs='?', default='.')
    p.add_argument('out', nargs='?')
    args = p.parse_args()
    repo = Path(args.repo)
    wf_dir = repo/'.github'/'workflows'
    blockers=[]; warnings=[]; files=[]
    if not wf_dir.exists():
        blockers.append('.github/workflows is missing')
    else:
        for name in sorted(BUILD_WORKFLOWS):
            path = wf_dir/name
            if path.exists():
                files.append(audit_file(path))
            else:
                warnings.append(f'{name} is missing')
    for f in files:
        for name, ok in f['checks'].items():
            if not ok:
                blockers.append(f"{f['workflow']} missing {name}")
    report={'phase':34,'workflow_files':files,'blockers':blockers,'warnings':warnings,'ready':not blockers}
    if args.out:
        out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
    else:
        print(json.dumps(report,indent=2,sort_keys=True))
    return 1 if blockers else 0
if __name__=='__main__':
    raise SystemExit(main())
