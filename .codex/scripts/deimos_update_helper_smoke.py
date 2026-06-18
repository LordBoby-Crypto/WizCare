#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, sys, tempfile
from pathlib import Path

def load_update_system(repo: Path):
    path = repo/'src/update_system.py'
    spec = importlib.util.spec_from_file_location('deimos_update_system_phase41', path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod

def main() -> int:
    repo = Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')
    out = Path(sys.argv[2]) if len(sys.argv)>2 else repo/'.codex/reports/phase41-update-helper-smoke.json'
    mod = load_update_system(repo)
    blockers=[]; warnings=[]
    with tempfile.TemporaryDirectory() as td:
        stage=Path(td)
        exe=stage/mod.STABLE_EXE_ASSET
        exe.write_bytes(b'deimos helper smoke exe')
        digest=hashlib.sha256(exe.read_bytes()).hexdigest()
        checksum=stage/mod.STABLE_CHECKSUM_ASSET
        checksum.write_text(f'{digest}  Deimos.exe\n', encoding='utf-8')
        manifest_file=stage/mod.STABLE_MANIFEST_ASSET
        manifest_file.write_text(json.dumps({'version':'smoke'}), encoding='utf-8')
        release=mod.ReleaseInfo(
            tag_name='v3.13.2', name='Smoke Release', html_url='https://example.invalid/release',
            prerelease=False, draft=False,
            assets={
                mod.STABLE_EXE_ASSET: mod.ReleaseAsset(mod.STABLE_EXE_ASSET, 'https://example.invalid/Deimos.exe', exe.stat().st_size),
                mod.STABLE_CHECKSUM_ASSET: mod.ReleaseAsset(mod.STABLE_CHECKSUM_ASSET, 'https://example.invalid/Deimos.exe.sha256', checksum.stat().st_size),
                mod.STABLE_MANIFEST_ASSET: mod.ReleaseAsset(mod.STABLE_MANIFEST_ASSET, 'https://example.invalid/release-manifest.json', manifest_file.stat().st_size),
            }, raw={}
        )
        helper_contract = mod.build_update_helper_contract()
        if helper_contract.get('helper_enabled') is not False:
            blockers.append('helper contract must not enable helper execution')
        helper_manifest = mod.build_update_helper_manifest(
            release,
            {mod.STABLE_EXE_ASSET: exe, mod.STABLE_CHECKSUM_ASSET: checksum, mod.STABLE_MANIFEST_ASSET: manifest_file},
            target_executable=stage/'installed'/'Deimos.exe',
            rollback_directory=stage/'rollback',
            install_log=stage/mod.HELPER_LOG_NAME,
            user_confirmed=False,
            created_at_utc='2026-06-16T00:00:00Z',
        )
        blockers_expected = mod.validate_update_helper_manifest(helper_manifest)
        if not any('user_confirmed' in b for b in blockers_expected):
            blockers.append('manifest validator should block unconfirmed helper launch')
        helper_manifest['user_confirmed'] = True
        blockers_confirmed = mod.validate_update_helper_manifest(helper_manifest)
        if blockers_confirmed:
            blockers.append('confirmed smoke manifest should validate: '+ '; '.join(blockers_confirmed))
    report={'phase':41,'script':'deimos_update_helper_smoke','passed':not blockers,'blockers':blockers,'warnings':warnings}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if not blockers else 1
if __name__=='__main__': raise SystemExit(main())
