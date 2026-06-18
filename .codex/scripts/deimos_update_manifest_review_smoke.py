#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, tempfile, sys
from pathlib import Path

def import_update_system(repo:Path):
    p=repo/'src/update_system.py'
    spec=importlib.util.spec_from_file_location('phase39_update_system',p)
    mod=importlib.util.module_from_spec(spec); assert spec and spec.loader
    sys.modules[spec.name]=mod; spec.loader.exec_module(mod); return mod

def main():
    repo=Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')
    out=Path(sys.argv[2]) if len(sys.argv)>2 else None
    blockers=[]; warnings=[]
    try:
        us=import_update_system(repo)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); stage=root/'stage'; stage.mkdir()
            exe=stage/us.STABLE_EXE_ASSET; exe.write_bytes(b'phase39 staged manifest review bytes')
            digest=hashlib.sha256(exe.read_bytes()).hexdigest()
            checksum=stage/us.STABLE_CHECKSUM_ASSET; checksum.write_text(f'{digest}  {us.STABLE_EXE_ASSET}\n',encoding='utf-8')
            manifest=stage/us.STABLE_MANIFEST_ASSET; manifest.write_text(json.dumps({'version':'v99.99.99','files':[{'name':us.STABLE_EXE_ASSET,'sha256':digest}]}),encoding='utf-8')
            release=us.ReleaseInfo(tag_name='v99.99.99',name='Smoke',html_url='https://example.invalid',prerelease=False,draft=False,assets={
                us.STABLE_EXE_ASSET:us.ReleaseAsset(us.STABLE_EXE_ASSET,'https://example.invalid/Deimos.exe',exe.stat().st_size),
                us.STABLE_CHECKSUM_ASSET:us.ReleaseAsset(us.STABLE_CHECKSUM_ASSET,'https://example.invalid/Deimos.exe.sha256',checksum.stat().st_size),
                us.STABLE_MANIFEST_ASSET:us.ReleaseAsset(us.STABLE_MANIFEST_ASSET,'https://example.invalid/release-manifest.json',manifest.stat().st_size),
            },raw={})
            review=us.build_staged_asset_review(release,{us.STABLE_EXE_ASSET:exe,us.STABLE_CHECKSUM_ASSET:checksum,us.STABLE_MANIFEST_ASSET:manifest})
            if review.get('checksum_status')!='verified': blockers.append(f"checksum not verified: {review.get('checksum_status')}")
            if not review.get('review_only') or not review.get('install_locked'): blockers.append('review must be locked/non-installing')
            if not review.get('manifest') or review['manifest'].get('version')!='v99.99.99': blockers.append('manifest JSON not parsed into review')
            if len(review.get('assets') or []) < 3: blockers.append('review did not include all stable assets')
            checksum.write_text('0'*64+f'  {us.STABLE_EXE_ASSET}\n',encoding='utf-8')
            bad=us.build_staged_asset_review(release,{us.STABLE_EXE_ASSET:exe,us.STABLE_CHECKSUM_ASSET:checksum,us.STABLE_MANIFEST_ASSET:manifest})
            if bad.get('checksum_status')!='mismatch': blockers.append('checksum mismatch not reported in review')
    except Exception as exc:
        blockers.append(str(exc))
    result={'ok':not blockers,'phase':39,'blockers':blockers,'warnings':warnings}
    if out:
        out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2)); return 1 if blockers else 0
if __name__=='__main__': raise SystemExit(main())
