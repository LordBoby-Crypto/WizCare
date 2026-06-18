#!/usr/bin/env python3
"""Report size and SHA-256 for a built deimos-updater-helper executable."""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

HELPER = Path("libs/updater_helper/dist/deimos-updater-helper.exe")
ALT_HELPER = Path("libs/updater_helper/dist/deimos-updater-helper")
CHECKSUM = Path("libs/updater_helper/dist/deimos-updater-helper.exe.sha256")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""): h.update(chunk)
    return h.hexdigest()


def parse_checksum(path: Path):
    text = path.read_text(encoding="utf-8").strip()
    parts = text.split()
    if not parts or not re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]):
        return None, None, "invalid checksum format"
    return parts[0].lower(), (parts[1] if len(parts)>1 else None), None


def report(repo: Path, write_checksum: bool, require_artifact: bool) -> dict:
    helper = repo / HELPER
    alt = repo / ALT_HELPER
    chosen = helper if helper.exists() else alt
    blockers=[]; warnings=[]
    exists = chosen.exists()
    digest=None; size=None; checksum_matches=None; checksum_path=repo/CHECKSUM
    if not exists:
        if require_artifact: blockers.append("built updater helper executable is required but missing")
        else: warnings.append("helper executable missing; report is in pre-build mode")
    else:
        size=chosen.stat().st_size
        digest=sha256(chosen)
        if write_checksum:
            checksum_path.parent.mkdir(parents=True, exist_ok=True)
            checksum_path.write_text(f"{digest}  deimos-updater-helper.exe\n", encoding="utf-8")
        if checksum_path.exists():
            expected, filename, err = parse_checksum(checksum_path)
            if err: blockers.append(err)
            else: checksum_matches = expected == digest and filename in (None, "deimos-updater-helper.exe", chosen.name)
            if checksum_matches is False: blockers.append("helper checksum file does not match helper executable")
        else:
            warnings.append("helper checksum file is absent")
    return {"phase":44,"artifact_path":str(chosen),"artifact_exists":exists,"artifact_size":size,"sha256":digest,"checksum_path":str(checksum_path),"checksum_matches":checksum_matches,"release_asset_name":"deimos-updater-helper.exe","checksum_asset_name":"deimos-updater-helper.exe.sha256","install_locked":True,"blockers":blockers,"warnings":warnings,"passed":not blockers}


def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("repo", nargs="?", default="."); p.add_argument("output", nargs="?", default=".codex/reports/phase44-helper-artifact-report.json"); p.add_argument("--write-checksum", action="store_true"); p.add_argument("--require-artifact", action="store_true")
    a=p.parse_args(argv); r=report(Path(a.repo).resolve(), a.write_checksum, a.require_artifact); out=Path(a.output); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(r,indent=2,sort_keys=True),encoding="utf-8"); print(json.dumps(r, sort_keys=True)); return 0 if r['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
