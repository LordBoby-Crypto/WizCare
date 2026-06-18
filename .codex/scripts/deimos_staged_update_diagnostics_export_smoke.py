#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import hashlib, importlib.util, json, sys, tempfile, zipfile


def load_update_system(root: Path):
    spec = importlib.util.spec_from_file_location('phase59_update_system', root/'src/update_system.py')
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod

def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')
    out = Path(sys.argv[2]) if len(sys.argv)>2 else root/'.codex/reports/phase59-diagnostics-export-smoke.json'
    mod = load_update_system(root)
    tmp = Path(tempfile.mkdtemp(prefix='deimos-phase59-'))
    stage = tmp/'stage'; stage.mkdir()
    exe = stage/'Deimos.exe'; exe.write_bytes(b'fake executable payload for diagnostics export')
    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    checksum = stage/'Deimos.exe.sha256'; checksum.write_text(f'{digest}  Deimos.exe\n', encoding='utf-8')
    manifest = stage/'release-manifest.json'; manifest.write_text(json.dumps({'version':'test','assets':[]}), encoding='utf-8')
    helper_manifest = stage/'deimos-helper-manifest.json'; helper_manifest.write_text(json.dumps({'schema_version':'1.0'}), encoding='utf-8')
    helper_log = stage/'deimos-updater-helper.log'; helper_log.write_text('\n'.join([
        json.dumps({'event':'plan_built'}),
        json.dumps({'event':'checksum_verified'}),
        json.dumps({'event':'dry_run_complete'}),
    ])+'\n', encoding='utf-8')
    release = mod.ReleaseInfo(
        tag_name='v9.9.9', name='Test Release', html_url='https://example.invalid/release', prerelease=False, draft=False,
        assets={
            'Deimos.exe': mod.ReleaseAsset('Deimos.exe','https://example.invalid/Deimos.exe', exe.stat().st_size),
            'Deimos.exe.sha256': mod.ReleaseAsset('Deimos.exe.sha256','https://example.invalid/Deimos.exe.sha256', checksum.stat().st_size),
            'release-manifest.json': mod.ReleaseAsset('release-manifest.json','https://example.invalid/release-manifest.json', manifest.stat().st_size),
        }, raw={}
    )
    staged = {'Deimos.exe':exe,'Deimos.exe.sha256':checksum,'release-manifest.json':manifest}
    bundle = mod.build_staged_update_diagnostics_bundle(release, staged)
    zip_path = tmp/'diagnostics.zip'
    mod.export_staged_update_diagnostics_bundle(release, staged, zip_path)
    names = []
    with zipfile.ZipFile(zip_path) as zf:
        names = sorted(zf.namelist())
        diag = json.loads(zf.read('deimos-staged-update-diagnostics.json').decode('utf-8'))
    blockers=[]
    if bundle['summary']['checksum_status'] != 'verified':
        blockers.append('bundle checksum was not verified')
    if 'Deimos.exe' in names or any(n.endswith('/Deimos.exe') for n in names):
        blockers.append('diagnostics zip must not include executable payload')
    for required in ['deimos-staged-update-diagnostics.json','README.txt','artifacts/Deimos.exe.sha256','artifacts/release-manifest.json','artifacts/deimos-helper-manifest.json','artifacts/deimos-updater-helper.log']:
        if required not in names:
            blockers.append(f'diagnostics zip missing {required}')
    if not diag.get('install_locked'):
        blockers.append('diagnostics object did not preserve install_locked=true')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({'phase':59,'passed':not blockers,'blockers':blockers,'zip_entries':names,'summary':diag.get('summary')}, indent=2), encoding='utf-8')
    return 1 if blockers else 0
if __name__ == '__main__':
    raise SystemExit(main())
