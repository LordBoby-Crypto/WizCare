#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, tempfile, sys
from pathlib import Path


def import_update_system(repo: Path):
    path = repo/'src/update_system.py'
    spec = importlib.util.spec_from_file_location('phase38_update_system', path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def main():
    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    blockers = []
    warnings = []
    try:
        us = import_update_system(repo)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root/'source'; source.mkdir()
            exe = source/us.STABLE_EXE_ASSET
            exe.write_bytes(b'Deimos staged update smoke test executable bytes\n')
            digest = hashlib.sha256(exe.read_bytes()).hexdigest()
            checksum = source/us.STABLE_CHECKSUM_ASSET
            checksum.write_text(f'{digest}  {us.STABLE_EXE_ASSET}\n', encoding='utf-8')
            manifest = source/us.STABLE_MANIFEST_ASSET
            manifest.write_text(json.dumps({'name': us.STABLE_EXE_ASSET, 'sha256': digest}), encoding='utf-8')
            release = us.ReleaseInfo(
                tag_name='v99.99.99', name='Smoke', html_url='https://example.invalid/release', prerelease=False, draft=False,
                assets={
                    us.STABLE_EXE_ASSET: us.ReleaseAsset(us.STABLE_EXE_ASSET, exe.as_uri(), exe.stat().st_size, 'application/octet-stream'),
                    us.STABLE_CHECKSUM_ASSET: us.ReleaseAsset(us.STABLE_CHECKSUM_ASSET, checksum.as_uri(), checksum.stat().st_size, 'text/plain'),
                    us.STABLE_MANIFEST_ASSET: us.ReleaseAsset(us.STABLE_MANIFEST_ASSET, manifest.as_uri(), manifest.stat().st_size, 'application/json'),
                }, raw={}
            )
            staged = us.stage_release_assets(release, root/'stage')
            for name in (us.STABLE_EXE_ASSET, us.STABLE_CHECKSUM_ASSET, us.STABLE_MANIFEST_ASSET):
                if name not in staged or not staged[name].exists(): blockers.append(f'missing staged asset {name}')
            if us.sha256_file(staged[us.STABLE_EXE_ASSET]) != digest: blockers.append('staged executable checksum mismatch')
            # Make sure checksum failures block.
            bad = source/'bad.sha256'; bad.write_text('0'*64 + f'  {us.STABLE_EXE_ASSET}\n', encoding='utf-8')
            bad_release = us.ReleaseInfo(
                tag_name='v99.99.99', name='SmokeBad', html_url=None, prerelease=False, draft=False,
                assets={
                    us.STABLE_EXE_ASSET: us.ReleaseAsset(us.STABLE_EXE_ASSET, exe.as_uri()),
                    us.STABLE_CHECKSUM_ASSET: us.ReleaseAsset(us.STABLE_CHECKSUM_ASSET, bad.as_uri()),
                }, raw={}
            )
            try:
                us.stage_release_assets(bad_release, root/'bad-stage')
                blockers.append('checksum mismatch did not block staged download')
            except Exception:
                pass
    except Exception as exc:
        blockers.append(str(exc))
    result = {'ok': not blockers, 'blockers': blockers, 'warnings': warnings}
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 1 if blockers else 0
if __name__ == '__main__': raise SystemExit(main())
