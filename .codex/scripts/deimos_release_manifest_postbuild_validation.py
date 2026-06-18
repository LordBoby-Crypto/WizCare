#!/usr/bin/env python3
"""Validate release-manifest.json after a real build.

Pre-build mode allows absent artifacts. Strict post-build mode requires
Deimos.exe, helper executable, checksum files, and manifest metadata to agree.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

PRIMARY = 'Deimos.exe'
PRIMARY_SHA = 'Deimos.exe.sha256'
MANIFEST = 'release-manifest.json'
HELPER = 'deimos-updater-helper.exe'
HELPER_SHA = 'deimos-updater-helper.exe.sha256'


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def checksum_matches(path: Path, digest: str, filename: str) -> tuple[bool, str]:
    if not path.exists():
        return False, 'checksum file missing'
    text = path.read_text(encoding='utf-8', errors='ignore').strip()
    parts = text.split()
    if not parts or not re.fullmatch(r'[0-9a-fA-F]{64}', parts[0]):
        return False, 'checksum file does not start with a 64-hex digest'
    if parts[0].lower() != digest:
        return False, 'checksum digest does not match artifact'
    if len(parts) > 1 and parts[1] != filename:
        return False, f'checksum filename is {parts[1]!r}, expected {filename!r}'
    return True, 'ok'


def helper_paths(repo: Path) -> tuple[Path, Path]:
    helper = repo / 'libs' / 'updater_helper' / 'dist' / HELPER
    helper_sha = repo / 'libs' / 'updater_helper' / 'dist' / HELPER_SHA
    if not helper.exists() and (repo / 'dist' / HELPER).exists():
        helper = repo / 'dist' / HELPER
        helper_sha = repo / 'dist' / HELPER_SHA
    return helper, helper_sha


def artifact_by_name(manifest: dict, name: str) -> dict | None:
    for item in manifest.get('artifacts') or []:
        if isinstance(item, dict) and item.get('name') == name:
            return item
    return None


def validate(repo: Path, require_manifest: bool, require_artifacts: bool, require_helper: bool) -> dict:
    dist = repo / 'dist'
    manifest_path = dist / MANIFEST
    exe = dist / PRIMARY
    exe_sha = dist / PRIMARY_SHA
    helper, helper_sha = helper_paths(repo)
    blockers=[]; warnings=[]; checks=[]
    manifest=None

    if not manifest_path.exists():
        msg='dist/release-manifest.json is missing'
        if require_manifest or require_artifacts: blockers.append(msg)
        else: warnings.append(msg + '; pre-build mode')
    else:
        try:
            manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
        except Exception as e:
            blockers.append(f'release manifest is invalid JSON: {e}')

    def add_artifact_check(name: str, path: Path, checksum_path: Path, required: bool):
        exists=path.exists(); row={'name':name,'path':str(path.relative_to(repo)) if path.is_relative_to(repo) else str(path),'exists':exists,'required':required}
        if not exists:
            (blockers if required else warnings).append(f'{name} is missing' + ('' if required else '; pre-build/optional'))
            checks.append(row); return
        digest=sha256(path); row['sha256']=digest; row['size_bytes']=path.stat().st_size
        ok, reason=checksum_matches(checksum_path, digest, name); row['checksum_path']=str(checksum_path.relative_to(repo)) if checksum_path.is_relative_to(repo) else str(checksum_path); row['checksum_matches']=ok; row['checksum_reason']=reason
        if not ok: blockers.append(f'{name} checksum invalid: {reason}')
        if manifest:
            art=artifact_by_name(manifest, name); row['manifest_entry_present']=bool(art)
            if not art: blockers.append(f'manifest missing artifact entry for {name}')
            else:
                if art.get('sha256') and art.get('sha256') != digest: blockers.append(f'manifest sha256 mismatch for {name}')
                if art.get('size_bytes') and art.get('size_bytes') != path.stat().st_size: blockers.append(f'manifest size mismatch for {name}')
            sha_art=artifact_by_name(manifest, name + '.sha256'); row['manifest_checksum_entry_present']=bool(sha_art)
            if not sha_art: blockers.append(f'manifest missing checksum artifact entry for {name}.sha256')
        checks.append(row)

    add_artifact_check(PRIMARY, exe, exe_sha, require_artifacts)
    add_artifact_check(HELPER, helper, helper_sha, require_helper)

    if manifest:
        contract=manifest.get('updater_contract') or {}
        stable=contract.get('stable_asset_names') or []
        for item in [PRIMARY, PRIMARY_SHA, MANIFEST]:
            if item not in stable: blockers.append(f'updater_contract.stable_asset_names missing {item}')
        helper_block=contract.get('updater_helper') or {}
        if require_helper and not helper_block: blockers.append('updater_contract.updater_helper missing in strict helper mode')
        if helper_block:
            if helper_block.get('executable') != HELPER: blockers.append('updater helper executable contract mismatch')
            if helper_block.get('checksum') != HELPER_SHA: blockers.append('updater helper checksum contract mismatch')
            if helper_block.get('launch_from_gui_locked') is not True: blockers.append('helper GUI launch must remain locked')
            if helper_block.get('install_execution_locked') is not True: blockers.append('helper install execution must remain locked')
            if require_helper and helper_block.get('postbuild_manifest_metadata_required') is not True: blockers.append('helper postbuild metadata flag must be true')
        if manifest.get('install_execution_locked') is not True: blockers.append('manifest install_execution_locked must be true')
        if manifest.get('gui_helper_launch_locked') is not True: blockers.append('manifest gui_helper_launch_locked must be true')

    return {'phase':48,'repo':str(repo),'manifest_path':str(manifest_path),'manifest_exists':manifest_path.exists(),'require_manifest':require_manifest,'require_artifacts':require_artifacts,'require_helper':require_helper,'artifact_checks':checks,'blockers':blockers,'warnings':warnings,'passed':not blockers}


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('repo', nargs='?', default='.')
    p.add_argument('output', nargs='?', default='.codex/reports/phase48-release-manifest-postbuild-validation.json')
    p.add_argument('--require-manifest', action='store_true')
    p.add_argument('--require-artifacts', action='store_true')
    p.add_argument('--require-helper', action='store_true')
    a=p.parse_args(argv)
    r=validate(Path(a.repo).resolve(), a.require_manifest, a.require_artifacts, a.require_helper)
    out=Path(a.output); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(r, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(r, sort_keys=True))
    return 0 if r['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
