#!/usr/bin/env python3
"""Validate helper metadata inside dist/release-manifest.json without enabling install execution."""
from __future__ import annotations
import argparse, json
from pathlib import Path

EXPECTED = {
    "helper_executable": "deimos-updater-helper.exe",
    "helper_checksum": "deimos-updater-helper.exe.sha256",
    "primary_executable": "Deimos.exe",
}

def load_manifest(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))

def report(repo: Path, require_manifest: bool=False) -> dict:
    manifest = repo / 'dist' / 'release-manifest.json'
    blockers=[]; warnings=[]; data=None; helper=None
    if not manifest.exists():
        if require_manifest: blockers.append('dist/release-manifest.json is required but missing')
        else: warnings.append('release manifest missing; helper integration is pre-build only')
    else:
        try: data=load_manifest(manifest)
        except Exception as e: blockers.append(f'release manifest is invalid JSON: {e}')
        if isinstance(data, dict):
            contract=data.get('updater_contract') or {}
            stable=contract.get('stable_asset_names') or []
            helper=contract.get('updater_helper') or data.get('updater_helper')
            for item in ['Deimos.exe','Deimos.exe.sha256','release-manifest.json']:
                if item not in stable: blockers.append(f'stable asset list missing {item}')
            for item in ['deimos-updater-helper.exe','deimos-updater-helper.exe.sha256']:
                if item not in stable: warnings.append(f'stable asset list missing optional helper asset {item}')
            if not helper:
                warnings.append('manifest has no updater_helper block yet')
            else:
                if helper.get('executable') != EXPECTED['helper_executable']: blockers.append('updater_helper.executable is not deimos-updater-helper.exe')
                if helper.get('checksum') != EXPECTED['helper_checksum']: blockers.append('updater_helper.checksum is not deimos-updater-helper.exe.sha256')
                if helper.get('launch_from_gui_locked') is not True: blockers.append('helper GUI launch must remain locked in manifest')
                if helper.get('install_execution_locked') is not True: blockers.append('helper install execution must remain locked in manifest')
    return {'phase':45,'manifest_path':str(manifest),'manifest_exists':manifest.exists(),'helper_block_present':bool(helper),'expected_helper_assets':[EXPECTED['helper_executable'],EXPECTED['helper_checksum']],'install_execution_locked':True,'gui_launch_locked':True,'blockers':blockers,'warnings':warnings,'passed':not blockers}

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('repo', nargs='?', default='.'); p.add_argument('output', nargs='?', default='.codex/reports/phase45-helper-manifest-integration.json'); p.add_argument('--require-manifest', action='store_true')
    a=p.parse_args(argv); r=report(Path(a.repo).resolve(), a.require_manifest); out=Path(a.output); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(r,indent=2,sort_keys=True),encoding='utf-8'); print(json.dumps(r, sort_keys=True)); return 0 if r['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
