#!/usr/bin/env python3
"""Validate the expected Deimos updater-helper executable artifact contract."""
from __future__ import annotations
import argparse, json, platform, re, sys
from pathlib import Path

EXPECTED_NAME = "deimos-updater-helper.exe"
EXPECTED_CHECKSUM = "deimos-updater-helper.exe.sha256"
EXPECTED_SOURCE = "libs/updater_helper/deimos_updater_helper.py"
EXPECTED_SPEC = "libs/updater_helper/deimos_updater_helper.spec"
EXPECTED_DIST = "libs/updater_helper/dist/deimos-updater-helper.exe"
EXPECTED_ALT_DIST = "libs/updater_helper/dist/deimos-updater-helper"
EXPECTED_BUILD_HELPER = "libs/updater_helper/build_helper.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def report(repo: Path, require_artifact: bool = False) -> dict:
    spec = repo / EXPECTED_SPEC
    build = repo / EXPECTED_BUILD_HELPER
    expected_exe = repo / EXPECTED_DIST
    alt_exe = repo / EXPECTED_ALT_DIST
    source = repo / EXPECTED_SOURCE
    spec_text = read_text(spec)
    build_text = read_text(build)
    blockers: list[str] = []
    warnings: list[str] = []

    if not source.exists(): blockers.append(f"missing {EXPECTED_SOURCE}")
    if not spec.exists(): blockers.append(f"missing {EXPECTED_SPEC}")
    if not build.exists(): blockers.append(f"missing {EXPECTED_BUILD_HELPER}")
    if spec.exists() and 'name="deimos-updater-helper"' not in spec_text and "name='deimos-updater-helper'" not in spec_text:
        blockers.append("helper PyInstaller spec must name the executable deimos-updater-helper")
    if build.exists() and "deimos-updater-helper" not in build_text:
        blockers.append("build_helper.py must reference the stable helper executable name")
    if build.exists() and "--build" not in build_text:
        warnings.append("build_helper.py does not expose an explicit --build flag")

    exists = expected_exe.exists() or alt_exe.exists()
    chosen = expected_exe if expected_exe.exists() else alt_exe
    if require_artifact and not exists:
        blockers.append(f"missing built helper artifact: {EXPECTED_DIST}")
    elif not exists:
        warnings.append("helper executable is absent; artifact validation is in pre-build mode")

    return {
        "phase": 44,
        "repo": str(repo),
        "expected_helper_asset": EXPECTED_NAME,
        "expected_checksum_asset": EXPECTED_CHECKSUM,
        "expected_artifact_path": EXPECTED_DIST,
        "artifact_exists": exists,
        "artifact_path": str(chosen) if exists else None,
        "platform": platform.system(),
        "install_locked": True,
        "gui_launch_locked": True,
        "blockers": blockers,
        "warnings": warnings,
        "passed": not blockers,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("repo", nargs="?", default=".")
    p.add_argument("output", nargs="?", default=".codex/reports/phase44-helper-artifact-contract.json")
    p.add_argument("--require-artifact", action="store_true")
    a = p.parse_args(argv)
    r = report(Path(a.repo).resolve(), a.require_artifact)
    out = Path(a.output); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(r, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(r, sort_keys=True))
    return 0 if r["passed"] else 1
if __name__ == "__main__": raise SystemExit(main())
