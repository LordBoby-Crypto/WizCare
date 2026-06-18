#!/usr/bin/env python3
"""Smoke-test the disabled install-design review with staged fake assets."""
from __future__ import annotations
import hashlib, importlib.util, json, sys, tempfile
from pathlib import Path

def load_update_system(root: Path):
    mod_path = root/'src/update_system.py'
    spec = importlib.util.spec_from_file_location('deimos_update_system_smoke', mod_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod

def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else root/'.codex/reports/phase40-install-design-smoke.json'
    us = load_update_system(root)
    with tempfile.TemporaryDirectory() as td:
        stage = Path(td)
        exe = stage/us.STABLE_EXE_ASSET
        exe.write_bytes(b'deimos fake exe bytes')
        sha = hashlib.sha256(exe.read_bytes()).hexdigest()
        checksum = stage/us.STABLE_CHECKSUM_ASSET
        checksum.write_text(f"{sha}  Deimos.exe\n", encoding='utf-8')
        manifest = stage/us.STABLE_MANIFEST_ASSET
        manifest.write_text(json.dumps({"version":"9.9.9","assets":["Deimos.exe"]}), encoding='utf-8')
        release = us.ReleaseInfo(
            tag_name='v9.9.9', name='Test', html_url='https://example.invalid', prerelease=False, draft=False,
            assets={
                us.STABLE_EXE_ASSET: us.ReleaseAsset(us.STABLE_EXE_ASSET,'https://example.invalid/Deimos.exe', exe.stat().st_size),
                us.STABLE_CHECKSUM_ASSET: us.ReleaseAsset(us.STABLE_CHECKSUM_ASSET,'https://example.invalid/Deimos.exe.sha256', checksum.stat().st_size),
                us.STABLE_MANIFEST_ASSET: us.ReleaseAsset(us.STABLE_MANIFEST_ASSET,'https://example.invalid/release-manifest.json', manifest.stat().st_size),
            }, raw={}
        )
        design = us.build_update_install_design_review(release, {
            us.STABLE_EXE_ASSET: exe,
            us.STABLE_CHECKSUM_ASSET: checksum,
            us.STABLE_MANIFEST_ASSET: manifest,
        })
    blockers=[]
    if design.get('install_enabled') is not False:
        blockers.append('install_enabled must remain false')
    if design.get('install_locked') is not True:
        blockers.append('install_locked must remain true')
    if design.get('checksum_verified') is not True:
        blockers.append('checksum should verify in smoke test')
    if not design.get('helper_required'):
        blockers.append('helper_required should be true')
    if not design.get('required_helper_process_behaviors'):
        blockers.append('helper behavior list missing')
    report={"passed": not blockers, "blockers": blockers, "design": design}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({"passed": report['passed'], "blockers": blockers}, indent=2))
    return 0 if not blockers else 1
if __name__ == '__main__':
    raise SystemExit(main())
