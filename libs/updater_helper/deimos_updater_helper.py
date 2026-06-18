#!/usr/bin/env python3
"""Dry-run-only updater helper scaffold for Deimos.

This file intentionally does not replace executables, relaunch Deimos, or mutate the
installation folder. It validates the future helper manifest contract and produces a
safe plan/log so the real helper can be implemented later with review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

EXIT_OK = 0
EXIT_MANIFEST_ERROR = 10
EXIT_CHECKSUM_ERROR = 11
EXIT_UNSAFE_OPERATION_BLOCKED = 12
EXIT_IO_ERROR = 13

REQUIRED_MANIFEST_FIELDS = {
    "schema_version",
    "operation",
    "current_exe",
    "staged_exe",
    "checksum_file",
    "rollback_dir",
}
ALLOWED_OPERATIONS = {"dry_run_replace_exe"}


@dataclass(frozen=True)
class HelperPlan:
    manifest_path: Path
    wait_pid: int
    log_path: Path
    current_exe: Path
    staged_exe: Path
    checksum_file: Path
    rollback_dir: Path
    dry_run: bool


def _write_log(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, sort_keys=True) + "\n")


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"manifest not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"manifest is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("manifest root must be a JSON object")
    missing = sorted(REQUIRED_MANIFEST_FIELDS - set(data))
    if missing:
        raise ValueError("manifest missing required fields: " + ", ".join(missing))
    if data.get("operation") not in ALLOWED_OPERATIONS:
        raise ValueError("manifest operation must be dry_run_replace_exe in this scaffold")
    return data


def _manifest_path(base: Path, value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (base / p).resolve()


def parse_checksum_file(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8").strip()
    m = re.match(r"^([a-fA-F0-9]{64})\s+(.+)$", text)
    if not m:
        raise ValueError("checksum file must be '<64-hex-sha256>  Deimos.exe'")
    return m.group(1).lower(), m.group(2).strip()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_plan(manifest_path: Path, wait_pid: int, log_path: Path, dry_run: bool) -> HelperPlan:
    manifest = _load_manifest(manifest_path)
    base = manifest_path.parent
    return HelperPlan(
        manifest_path=manifest_path,
        wait_pid=wait_pid,
        log_path=log_path,
        current_exe=_manifest_path(base, str(manifest["current_exe"])),
        staged_exe=_manifest_path(base, str(manifest["staged_exe"])),
        checksum_file=_manifest_path(base, str(manifest["checksum_file"])),
        rollback_dir=_manifest_path(base, str(manifest["rollback_dir"])),
        dry_run=dry_run,
    )


def validate_plan(plan: HelperPlan) -> list[str]:
    blockers: list[str] = []
    if not plan.dry_run:
        blockers.append("Phase 42 helper scaffold only allows --dry-run")
    if plan.wait_pid <= 0:
        blockers.append("--wait-pid must be a positive integer")
    if not plan.staged_exe.exists():
        blockers.append(f"staged executable not found: {plan.staged_exe}")
    if not plan.checksum_file.exists():
        blockers.append(f"checksum file not found: {plan.checksum_file}")
    if plan.current_exe.name.lower() != "deimos.exe":
        blockers.append("current_exe must point to Deimos.exe")
    if plan.staged_exe.name.lower() != "deimos.exe":
        blockers.append("staged_exe must be named Deimos.exe")
    if plan.rollback_dir == plan.current_exe.parent:
        blockers.append("rollback_dir must not be the install directory itself")
    return blockers


def verify_checksum(plan: HelperPlan) -> None:
    expected_hash, expected_name = parse_checksum_file(plan.checksum_file)
    if expected_name != "Deimos.exe":
        raise ValueError("checksum filename must be Deimos.exe")
    actual_hash = sha256_file(plan.staged_exe)
    if actual_hash != expected_hash:
        raise ValueError(f"checksum mismatch: expected {expected_hash}, got {actual_hash}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deimos updater helper scaffold (dry-run only)")
    parser.add_argument("--manifest", required=True, help="Path to deimos-helper-manifest.json")
    parser.add_argument("--wait-pid", required=True, type=int, help="PID of running Deimos process")
    parser.add_argument("--log", required=True, help="Path to helper JSONL log")
    parser.add_argument("--dry-run", action="store_true", help="Required in Phase 42")
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--relaunch", default=None, help="Accepted for contract compatibility; ignored in dry run")
    args = parser.parse_args(argv)

    log_path = Path(args.log).resolve()
    try:
        plan = build_plan(Path(args.manifest).resolve(), args.wait_pid, log_path, args.dry_run)
        blockers = validate_plan(plan)
        event = {"phase": 42, "event": "plan_built", "dry_run": plan.dry_run, "blockers": blockers}
        _write_log(log_path, event)
        if blockers:
            return EXIT_UNSAFE_OPERATION_BLOCKED
        verify_checksum(plan)
        _write_log(log_path, {"phase": 42, "event": "checksum_verified", "staged_exe": str(plan.staged_exe)})
        _write_log(log_path, {"phase": 42, "event": "dry_run_complete", "would_replace": False, "would_relaunch": False})
        print(json.dumps({"ok": True, "dry_run": True, "install_locked": True}, sort_keys=True))
        return EXIT_OK
    except ValueError as exc:
        _write_log(log_path, {"phase": 42, "event": "manifest_or_checksum_error", "error": str(exc)})
        print(str(exc), file=sys.stderr)
        return EXIT_MANIFEST_ERROR
    except OSError as exc:
        _write_log(log_path, {"phase": 42, "event": "io_error", "error": str(exc)})
        print(str(exc), file=sys.stderr)
        return EXIT_IO_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
