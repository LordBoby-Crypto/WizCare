#!/usr/bin/env python3
"""Report Deimos main/helper release artifact readiness and checksum status."""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

ASSETS=[('Deimos.exe','Deimos.exe.sha256', True),('deimos-updater-helper.exe','deimos-updater-helper.exe.sha256', False),('release-manifest.json',None, True)]

def sha256(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def check_checksum(path: Path, expected_name: str, digest: str):
    if not path.exists(): return None, 'missing checksum file'
    text=path.read_text(encoding='utf-8', errors='replace').strip(); parts=text.split()
    if not parts or not re.fullmatch(r'[0-9a-fA-F]{64}', parts[0]): return False, 'invalid checksum format'
    filename=parts[1] if len(parts)>1 else None
    return (parts[0].lower()==digest and filename in (None, expected_name)), None

def report(repo: Path, require_required: bool=False, require_helper: bool=False):
    dist=repo/'dist'; rows=[]; blockers=[]; warnings=[]
    for name, checksum_name, required in ASSETS:
        p=dist/name; row={'name':name,'path':str(p),'required':required,'exists':p.exists()}
        if p.exists() and p.is_file():
            row['size_bytes']=p.stat().st_size
            if name.endswith('.exe'):
                digest=sha256(p); row['sha256']=digest
                if checksum_name:
                    ok, issue=check_checksum(dist/checksum_name, name, digest); row['checksum_matches']=ok; row['checksum_issue']=issue
        else:
            if required and require_required: blockers.append(f'missing required release asset {name}')
            elif (name.startswith('deimos-updater-helper') and require_helper): blockers.append(f'missing helper release asset {name}')
            else: warnings.append(f'{name} is absent; matrix is in pre-build/pre-helper mode')
        rows.append(row)
    return {'phase':45,'release_asset_matrix':rows,'required_assets':['Deimos.exe','Deimos.exe.sha256','release-manifest.json'],'helper_assets':['deimos-updater-helper.exe','deimos-updater-helper.exe.sha256'],'install_execution_locked':True,'blockers':blockers,'warnings':warnings,'passed':not blockers}

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('repo', nargs='?', default='.'); p.add_argument('output', nargs='?', default='.codex/reports/phase45-helper-release-asset-matrix.json'); p.add_argument('--require-required', action='store_true'); p.add_argument('--require-helper', action='store_true')
    a=p.parse_args(argv); r=report(Path(a.repo).resolve(), a.require_required, a.require_helper); out=Path(a.output); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(r,indent=2,sort_keys=True),encoding='utf-8'); print(json.dumps(r, sort_keys=True)); return 0 if r['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
