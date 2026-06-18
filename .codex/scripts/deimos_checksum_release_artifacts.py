#!/usr/bin/env python3
"""Generate and verify Deimos release checksums and manifest files.

Phase 48: helper-aware manifest generation. The release manifest can now
include updater-helper artifact metadata from libs/updater_helper/dist while
keeping install execution locked.
"""
from __future__ import annotations
import argparse, hashlib, json, platform, re
from datetime import datetime, timezone
from pathlib import Path

PRIMARY_EXE = 'Deimos.exe'
PRIMARY_SHA = 'Deimos.exe.sha256'
MANIFEST = 'release-manifest.json'
HELPER_EXE = 'deimos-updater-helper.exe'
HELPER_SHA = 'deimos-updater-helper.exe.sha256'


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read_version(repo: Path) -> str | None:
    deimos = repo / 'Deimos.py'
    if not deimos.exists():
        return None
    text = deimos.read_text(encoding='utf-8', errors='ignore')
    m = re.search(r"tool_version:\s*str\s*=\s*['\"]([^'\"]+)['\"]", text)
    return m.group(1) if m else None


def helper_candidates(repo: Path) -> list[Path]:
    return [
        repo / 'dist' / HELPER_EXE,
        repo / 'libs' / 'updater_helper' / 'dist' / HELPER_EXE,
        repo / 'libs' / 'updater_helper' / 'dist' / 'deimos-updater-helper',
    ]


def find_existing(paths: list[Path]) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None


def checksum_text(digest: str, filename: str) -> str:
    return f'{digest}  {filename}\n'


def artifact_entry(name: str, path: Path, repo: Path, digest: str | None = None, extra: dict | None = None) -> dict:
    rel = path.relative_to(repo).as_posix() if path.is_relative_to(repo) else str(path)
    item = {'name': name, 'path': rel, 'exists': path.exists()}
    if path.exists():
        item['size_bytes'] = path.stat().st_size
    if digest:
        item['sha256'] = digest
    if extra:
        item.update(extra)
    return item


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('repo', nargs='?', default='.')
    p.add_argument('out', nargs='?')
    p.add_argument('--write', action='store_true', help='write dist/Deimos.exe.sha256 and dist/release-manifest.json when dist/Deimos.exe exists')
    p.add_argument('--require-artifact', action='store_true')
    p.add_argument('--require-helper-artifact', action='store_true', help='require helper executable/checksum when writing or validating release manifests')
    args = p.parse_args()

    repo = Path(args.repo).resolve()
    dist = repo / 'dist'
    exe = dist / PRIMARY_EXE
    sha_path = dist / PRIMARY_SHA
    manifest_path = dist / MANIFEST
    helper_exe = find_existing(helper_candidates(repo))
    helper_sha_path = (helper_exe.parent / HELPER_SHA) if helper_exe else (repo / 'libs' / 'updater_helper' / 'dist' / HELPER_SHA)

    blockers: list[str] = []
    warnings: list[str] = []
    artifact = {'path': 'dist/Deimos.exe', 'exists': exe.exists()}
    helper_artifact_report = {'expected_name': HELPER_EXE, 'exists': bool(helper_exe), 'path': str(helper_exe.relative_to(repo)) if helper_exe and helper_exe.is_relative_to(repo) else None}
    version = read_version(repo)

    if exe.exists():
        digest = sha256(exe)
        size = exe.stat().st_size
        artifact.update({'size_bytes': size, 'sha256': digest})
        if size < 5_000_000:
            warnings.append('dist/Deimos.exe is smaller than expected for a bundled GUI executable')

        helper_digest = None
        helper_artifact = None
        helper_checksum_artifact = None
        if helper_exe and helper_exe.exists():
            helper_digest = sha256(helper_exe)
            helper_artifact_report.update({'size_bytes': helper_exe.stat().st_size, 'sha256': helper_digest})
            if args.write:
                helper_sha_path.parent.mkdir(parents=True, exist_ok=True)
                helper_sha_path.write_text(checksum_text(helper_digest, HELPER_EXE), encoding='utf-8')
            helper_artifact = artifact_entry(HELPER_EXE, helper_exe, repo, helper_digest, {'role': 'updater-helper', 'install_execution_locked': True, 'gui_launch_locked': True})
            helper_checksum_artifact = artifact_entry(HELPER_SHA, helper_sha_path, repo, None, {'checksum_for': HELPER_EXE, 'algorithm': 'sha256', 'role': 'updater-helper-checksum'})
        elif args.require_helper_artifact:
            blockers.append('updater helper executable is required but missing')
        else:
            warnings.append('updater helper executable is not present; helper manifest integration is pre-build/optional')

        if args.write:
            dist.mkdir(parents=True, exist_ok=True)
            sha_path.write_text(checksum_text(digest, PRIMARY_EXE), encoding='utf-8')
            artifacts = [
                artifact_entry(PRIMARY_EXE, exe, repo, digest, {'role': 'primary-executable'}),
                artifact_entry(PRIMARY_SHA, sha_path, repo, None, {'checksum_for': PRIMARY_EXE, 'algorithm': 'sha256', 'role': 'primary-checksum'}),
                artifact_entry(MANIFEST, manifest_path, repo, None, {'role': 'release-manifest'}),
            ]
            if helper_artifact:
                artifacts.append(helper_artifact)
            if helper_checksum_artifact:
                artifacts.append(helper_checksum_artifact)
            manifest = {
                'application': 'Deimos',
                'manifest_schema_version': '1.1',
                'version': version,
                'created_utc': datetime.now(timezone.utc).isoformat(),
                'platform': platform.platform(),
                'updater_contract': {
                    'stable_asset_names': [PRIMARY_EXE, PRIMARY_SHA, MANIFEST, HELPER_EXE, HELPER_SHA],
                    'checksum_algorithm': 'sha256',
                    'checksum_file_format': '<64-hex-sha256>  <asset-name>',
                    'primary_executable': PRIMARY_EXE,
                    'primary_checksum': PRIMARY_SHA,
                    'release_manifest': MANIFEST,
                    'updater_helper': {
                        'executable': HELPER_EXE,
                        'checksum': HELPER_SHA,
                        'checksum_file_format': '<64-hex-sha256>  deimos-updater-helper.exe',
                        'launch_from_gui_locked': True,
                        'install_execution_locked': True,
                        'postbuild_manifest_metadata_required': True,
                    },
                },
                'artifacts': artifacts,
                'release_requirements': [PRIMARY_EXE, PRIMARY_SHA, MANIFEST],
                'helper_requirements_postbuild': [HELPER_EXE, HELPER_SHA],
                'install_execution_locked': True,
                'gui_helper_launch_locked': True,
            }
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding='utf-8')

        if sha_path.exists():
            txt = sha_path.read_text(encoding='utf-8', errors='ignore').strip()
            artifact['sha256_file_exists'] = True
            artifact['sha256_file_text'] = txt
            artifact['sha256_file_matches'] = digest in txt and PRIMARY_EXE in txt
            if not artifact['sha256_file_matches']:
                blockers.append('dist/Deimos.exe.sha256 exists but does not match dist/Deimos.exe')
        else:
            artifact['sha256_file_exists'] = False
            if args.require_artifact:
                blockers.append('dist/Deimos.exe.sha256 is missing')
            else:
                warnings.append('dist/Deimos.exe.sha256 is missing until post-build checksum generation runs')
        artifact['manifest_exists'] = manifest_path.exists()
        if args.require_artifact and not manifest_path.exists():
            blockers.append('dist/release-manifest.json is missing')
    else:
        if args.require_artifact:
            blockers.append('dist/Deimos.exe is missing')
        else:
            warnings.append('dist/Deimos.exe is not present; checksum/manifest validation is pre-build only')

    report = {
        'phase': 48,
        'repo': str(repo),
        'version': version,
        'write_requested': args.write,
        'require_artifact': args.require_artifact,
        'require_helper_artifact': args.require_helper_artifact,
        'artifact': artifact,
        'helper_artifact': helper_artifact_report,
        'blockers': blockers,
        'warnings': warnings,
        'ready': not blockers,
    }
    if args.out:
        out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding='utf-8')
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if blockers else 0

if __name__ == '__main__':
    raise SystemExit(main())
