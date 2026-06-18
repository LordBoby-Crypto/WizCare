#!/usr/bin/env python3
"""Phase 55 staged helper dry-run log generator.

Generate a real helper dry-run JSONL log from an already-staged update folder.
This script is intentionally safe: it only calls the Python updater-helper scaffold
with --dry-run. It never replaces Deimos.exe, relaunches Deimos, or enables GUI
helper launch behavior.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

STAGED_EXE = "Deimos.exe"
STAGED_CHECKSUM = "Deimos.exe.sha256"
HELPER_MANIFEST = "deimos-helper-manifest.json"
HELPER_LOG = "deimos-updater-helper.log"
ROLLBACK_DIR = "rollback"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_checksum(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8").strip().splitlines()[0]
    parts = text.split()
    if len(parts) < 2 or len(parts[0]) != 64:
        raise ValueError("checksum file must be '<64-hex-sha256>  Deimos.exe'")
    return parts[0].lower(), parts[-1]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
            rows.append(value if isinstance(value, dict) else {"raw": value})
        except json.JSONDecodeError:
            rows.append({"raw": line})
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def build_manifest(repo_root: Path, stage_dir: Path, current_exe: Path | None = None) -> dict[str, Any]:
    current = current_exe or (repo_root / "dist" / STAGED_EXE)
    return {
        "schema_version": 1,
        "operation": "dry_run_replace_exe",
        "current_exe": str(current.resolve()),
        "staged_exe": str((stage_dir / STAGED_EXE).resolve()),
        "checksum_file": str((stage_dir / STAGED_CHECKSUM).resolve()),
        "rollback_dir": str((stage_dir / ROLLBACK_DIR).resolve()),
        "phase": 55,
        "simulation_only": True,
        "install_locked": True,
        "gui_helper_launch_enabled": False,
    }


def generate(repo_root: Path, stage_dir: Path, wait_pid: int, out: Path | None = None, current_exe: Path | None = None) -> dict[str, Any]:
    helper = repo_root / "libs" / "updater_helper" / "deimos_updater_helper.py"
    blockers: list[str] = []
    warnings: list[str] = []
    if not helper.exists():
        blockers.append(f"helper scaffold missing: {helper}")
    exe = stage_dir / STAGED_EXE
    checksum = stage_dir / STAGED_CHECKSUM
    if not exe.exists():
        blockers.append(f"staged Deimos.exe missing: {exe}")
    if not checksum.exists():
        blockers.append(f"staged checksum missing: {checksum}")
    expected = actual = None
    if exe.exists() and checksum.exists():
        expected, checksum_name = parse_checksum(checksum)
        actual = sha256_file(exe)
        if checksum_name != STAGED_EXE:
            blockers.append("checksum filename must be Deimos.exe")
        if expected != actual:
            blockers.append("staged Deimos.exe checksum mismatch")
    manifest = stage_dir / HELPER_MANIFEST
    log = stage_dir / HELPER_LOG
    if blockers:
        payload = {
            "phase": 55,
            "passed": False,
            "simulation_only": True,
            "real_install_attempted": False,
            "install_execution_enabled": False,
            "helper_launch_from_gui_enabled": False,
            "blockers": blockers,
            "warnings": warnings,
            "stage_dir": str(stage_dir),
        }
        if out:
            write_json(out, payload)
        return payload
    stage_dir.mkdir(parents=True, exist_ok=True)
    (stage_dir / ROLLBACK_DIR).mkdir(parents=True, exist_ok=True)
    write_json(manifest, build_manifest(repo_root, stage_dir, current_exe=current_exe))
    if log.exists():
        log.unlink()
    cmd = [sys.executable, str(helper), "--manifest", str(manifest), "--wait-pid", str(wait_pid), "--log", str(log), "--dry-run"]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    events = read_jsonl(log)
    event_names = [str(e.get("event")) for e in events]
    required = ["plan_built", "checksum_verified", "dry_run_complete"]
    missing_events = [e for e in required if e not in event_names]
    payload = {
        "phase": 55,
        "name": "staged helper dry-run log generation",
        "passed": proc.returncode == 0 and not missing_events,
        "simulation_only": True,
        "real_install_attempted": False,
        "install_execution_enabled": False,
        "helper_launch_from_gui_enabled": False,
        "non_dry_run_enabled": False,
        "stage_dir": str(stage_dir),
        "manifest": str(manifest),
        "helper_log": str(log),
        "expected_sha256": expected,
        "actual_sha256": actual,
        "command": cmd,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
        "event_names": event_names,
        "missing_required_events": missing_events,
        "blockers": [] if proc.returncode == 0 and not missing_events else ["helper dry-run log generation failed or missing required events"],
        "warnings": warnings,
    }
    if out:
        write_json(out, payload)
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate a helper dry-run JSONL log from staged Deimos update files.")
    ap.add_argument("repo_root", help="Path to the Deimos repo root")
    ap.add_argument("stage_dir", help="Folder containing Deimos.exe and Deimos.exe.sha256")
    ap.add_argument("out", nargs="?", help="Optional JSON report path")
    ap.add_argument("--wait-pid", type=int, default=99999)
    ap.add_argument("--current-exe", help="Optional current Deimos.exe target path for manifest preview")
    args = ap.parse_args()
    payload = generate(Path(args.repo_root).resolve(), Path(args.stage_dir).resolve(), args.wait_pid, Path(args.out).resolve() if args.out else None, Path(args.current_exe).resolve() if args.current_exe else None)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
