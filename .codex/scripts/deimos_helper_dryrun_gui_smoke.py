#!/usr/bin/env python3
from pathlib import Path
import json, sys, tempfile, hashlib

def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else root/'.codex/reports/phase54-helper-dryrun-gui-smoke.json'
    sys.path.insert(0, str(root))
    from src.update_system import ReleaseAsset, ReleaseInfo, STABLE_EXE_ASSET, STABLE_CHECKSUM_ASSET, STABLE_MANIFEST_ASSET, HELPER_LOG_NAME, build_helper_dry_run_review
    with tempfile.TemporaryDirectory() as td:
        stage=Path(td)
        exe=stage/STABLE_EXE_ASSET; exe.write_bytes(b'phase54 fake exe')
        digest=hashlib.sha256(exe.read_bytes()).hexdigest()
        sha=stage/STABLE_CHECKSUM_ASSET; sha.write_text(f'{digest}  {STABLE_EXE_ASSET}\n', encoding='utf-8')
        manifest=stage/STABLE_MANIFEST_ASSET; manifest.write_text(json.dumps({'phase':54,'assets':[STABLE_EXE_ASSET]}), encoding='utf-8')
        log=stage/HELPER_LOG_NAME; log.write_text('\n'.join([json.dumps({'event':'manifest_loaded'}),json.dumps({'event':'checksum_verified'}),json.dumps({'event':'dry_run_complete'})])+'\n', encoding='utf-8')
        release=ReleaseInfo(tag_name='v9.9.9', name='Fake', html_url=None, prerelease=False, draft=False, assets={
            STABLE_EXE_ASSET: ReleaseAsset(STABLE_EXE_ASSET, 'file://fake', exe.stat().st_size),
            STABLE_CHECKSUM_ASSET: ReleaseAsset(STABLE_CHECKSUM_ASSET, 'file://fake', sha.stat().st_size),
            STABLE_MANIFEST_ASSET: ReleaseAsset(STABLE_MANIFEST_ASSET, 'file://fake', manifest.stat().st_size),
        }, raw={})
        review=build_helper_dry_run_review(release, {STABLE_EXE_ASSET:exe, STABLE_CHECKSUM_ASSET:sha, STABLE_MANIFEST_ASSET:manifest})
    blockers=[]
    if review.get('checksum_status')!='verified': blockers.append('checksum was not verified')
    if review.get('helper_launch_enabled') is not False: blockers.append('helper_launch_enabled not false')
    if review.get('install_execution_enabled') is not False: blockers.append('install_execution_enabled not false')
    events=[e.get('event') for e in review.get('helper_log_events', [])]
    for ev in ['manifest_loaded','checksum_verified','dry_run_complete']:
        if ev not in events: blockers.append(f'missing log event {ev}')
    result={'passed': not blockers, 'blockers': blockers, 'review_summary': {k: review.get(k) for k in ['review_only','checksum_status','helper_launch_enabled','install_execution_enabled','helper_log_status']}}
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 0 if not blockers else 1
if __name__ == '__main__': raise SystemExit(main())
