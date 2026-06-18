#!/usr/bin/env python3
"""Check release-manifest/updater contract rules for the future helper artifact."""
from __future__ import annotations
import argparse, json
from pathlib import Path


def report(repo: Path, require_manifest: bool=False) -> dict:
    manifest = repo / "dist" / "release-manifest.json"
    blockers=[]; warnings=[]; data=None; helper_block=None
    if not manifest.exists():
        if require_manifest: blockers.append("dist/release-manifest.json is required but missing")
        else: warnings.append("release manifest absent; helper inclusion check is in pre-build mode")
    else:
        try:
            data=json.loads(manifest.read_text(encoding='utf-8'))
        except Exception as e:
            blockers.append(f"release manifest is invalid JSON: {e}")
            data=None
        if isinstance(data, dict):
            helper_block = data.get('updater_helper') or data.get('helper') or (data.get('updater_contract') or {}).get('updater_helper')
            if not helper_block:
                warnings.append("release manifest does not yet include an updater_helper block")
            else:
                text=json.dumps(helper_block, sort_keys=True)
                for token in ["deimos-updater-helper.exe", "deimos-updater-helper.exe.sha256"]:
                    if token not in text: blockers.append(f"updater_helper manifest block missing {token}")
    return {"phase":44,"manifest_path":str(manifest),"manifest_exists":manifest.exists(),"helper_manifest_block_present":bool(helper_block),"expected_helper_assets":["deimos-updater-helper.exe","deimos-updater-helper.exe.sha256"],"install_locked":True,"blockers":blockers,"warnings":warnings,"passed":not blockers}


def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("repo", nargs="?", default="."); p.add_argument("output", nargs="?", default=".codex/reports/phase44-helper-manifest-inclusion.json"); p.add_argument("--require-manifest", action="store_true")
    a=p.parse_args(argv); r=report(Path(a.repo).resolve(), a.require_manifest); out=Path(a.output); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(r, indent=2, sort_keys=True), encoding='utf-8'); print(json.dumps(r, sort_keys=True)); return 0 if r['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
