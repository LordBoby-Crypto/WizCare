#!/usr/bin/env python3
"""Phase 53 helper install dry-run harness integration.

This script connects the Phase 42 updater-helper scaffold to the Phase 52 fake
install harness contract. It builds a temporary fake release/install filesystem,
runs the helper through its real manifest/log/checksum pathway in --dry-run mode,
and then runs the fake install harness scenarios. It never touches the real
Deimos executable and never runs non-dry-run helper behavior.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER = REPO_ROOT / "libs" / "updater_helper" / "deimos_updater_helper.py"
HARNESS = REPO_ROOT / ".codex" / "scripts" / "deimos_update_install_test_harness.py"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def build_fake_helper_environment(root: Path) -> dict[str, Path | str]:
    install_dir = root / "install"
    staged_dir = root / "staged"
    rollback_dir = root / "rollback"
    install_dir.mkdir(parents=True, exist_ok=True)
    staged_dir.mkdir(parents=True, exist_ok=True)
    rollback_dir.mkdir(parents=True, exist_ok=True)
    current_exe = install_dir / "Deimos.exe"
    staged_exe = staged_dir / "Deimos.exe"
    checksum_file = staged_dir / "Deimos.exe.sha256"
    manifest = staged_dir / "deimos-helper-manifest.json"
    log = root / "deimos-updater-helper.log"
    current_exe.write_bytes(b"PHASE53-FAKE-CURRENT-DEIMOS\n")
    staged_bytes = b"PHASE53-FAKE-STAGED-DEIMOS\n"
    staged_exe.write_bytes(staged_bytes)
    digest = sha256_bytes(staged_bytes)
    checksum_file.write_text(f"{digest}  Deimos.exe\n", encoding="utf-8")
    write_json(manifest, {
        "schema_version": 1,
        "operation": "dry_run_replace_exe",
        "current_exe": str(current_exe),
        "staged_exe": str(staged_exe),
        "checksum_file": str(checksum_file),
        "rollback_dir": str(rollback_dir),
        "phase": 53,
        "simulation_only": True,
    })
    return {
        "root": root,
        "current_exe": current_exe,
        "staged_exe": staged_exe,
        "checksum_file": checksum_file,
        "manifest": manifest,
        "log": log,
        "expected_sha256": digest,
    }


def run_helper(env: dict[str, Any]) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(HELPER),
        "--manifest", str(env["manifest"]),
        "--wait-pid", "99999",
        "--log", str(env["log"]),
        "--dry-run",
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    log_rows = read_jsonl(env["log"])
    events = [row.get("event") for row in log_rows]
    return {
        "command": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "log_events": events,
        "dry_run_complete": "dry_run_complete" in events,
        "checksum_verified": "checksum_verified" in events,
        "helper_ok": proc.returncode == 0 and "dry_run_complete" in events and "checksum_verified" in events,
    }


def run_harness_scenarios(work_dir: Path) -> dict[str, Any]:
    out = work_dir / "phase53-harness-scenarios.json"
    proc = subprocess.run([sys.executable, str(HARNESS), str(out), "--scenario", "all"], text=True, capture_output=True)
    payload: dict[str, Any] = {}
    if out.exists():
        payload = json.loads(out.read_text(encoding="utf-8"))
    return {
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-1000:],
        "stderr_tail": proc.stderr[-1000:],
        "payload": payload,
        "harness_ok": proc.returncode == 0 and bool(payload.get("passed")),
    }


def run_all(keep_temp: bool = False) -> dict[str, Any]:
    temp = Path(tempfile.mkdtemp(prefix="deimos-phase53-helper-harness-"))
    try:
        env = build_fake_helper_environment(temp)
        helper = run_helper(env)
        harness = run_harness_scenarios(temp)
        payload = {
            "phase": 53,
            "name": "helper install dry-run harness integration",
            "simulation_only": True,
            "real_install_attempted": False,
            "install_execution_enabled": False,
            "helper_launch_from_gui_enabled": False,
            "non_dry_run_enabled": False,
            "helper_result": helper,
            "harness_result": harness,
            "passed": helper["helper_ok"] and harness["harness_ok"],
            "blockers": [],
        }
        if not payload["passed"]:
            payload["blockers"].append("helper dry-run and install harness integration did not both pass")
        payload["temp_root"] = str(temp) if keep_temp else "removed"
        return payload
    finally:
        if not keep_temp:
            shutil.rmtree(temp, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Run Phase 53 helper-to-install-harness dry-run integration.")
    ap.add_argument("out", nargs="?", help="Optional JSON output path")
    ap.add_argument("--keep-temp", action="store_true")
    args = ap.parse_args()
    payload = run_all(keep_temp=args.keep_temp)
    if args.out:
        write_json(Path(args.out), payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
