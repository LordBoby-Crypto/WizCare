#!/usr/bin/env python3
"""Preflight/build wrapper for the Deimos updater helper PyInstaller scaffold."""
from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import subprocess
import sys
from pathlib import Path

HELPER_DIR = Path(__file__).resolve().parent
SPEC = HELPER_DIR / "deimos_updater_helper.spec"
SOURCE = HELPER_DIR / "deimos_updater_helper.py"
EXPECTED_EXE = HELPER_DIR / "dist" / ("deimos-updater-helper.exe" if platform.system() == "Windows" else "deimos-updater-helper")


def build_report() -> dict:
    pyinstaller_available = importlib.util.find_spec("PyInstaller") is not None
    return {
        "phase": 43,
        "helper_dir": str(HELPER_DIR),
        "source_exists": SOURCE.exists(),
        "spec_exists": SPEC.exists(),
        "pyinstaller_importable": pyinstaller_available,
        "platform": platform.system(),
        "expected_executable": str(EXPECTED_EXE),
        "build_command": [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", str(SPEC)],
        "uv_build_command": ["uv", "run", "--group", "dev", "pyinstaller", "--noconfirm", "--clean", str(SPEC)],
        "install_locked": True,
        "gui_launch_locked": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build/preflight Deimos updater helper")
    parser.add_argument("--report", help="Write JSON report to this path")
    parser.add_argument("--build", action="store_true", help="Actually run PyInstaller; off by default")
    args = parser.parse_args(argv)

    report = build_report()
    blockers = []
    if not report["source_exists"]:
        blockers.append("missing libs/updater_helper/deimos_updater_helper.py")
    if not report["spec_exists"]:
        blockers.append("missing libs/updater_helper/deimos_updater_helper.spec")
    if args.build and not report["pyinstaller_importable"]:
        blockers.append("PyInstaller is not importable in this environment")
    report["blockers"] = blockers

    if args.build and not blockers:
        proc = subprocess.run(report["build_command"], cwd=str(HELPER_DIR), text=True)
        report["build_exit_code"] = proc.returncode
        report["expected_executable_exists"] = EXPECTED_EXE.exists()
        if proc.returncode != 0:
            blockers.append(f"PyInstaller exited with {proc.returncode}")
        if not EXPECTED_EXE.exists():
            blockers.append(f"expected helper executable not found: {EXPECTED_EXE}")
        report["blockers"] = blockers

    if args.report:
        path = Path(args.report)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 1 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
