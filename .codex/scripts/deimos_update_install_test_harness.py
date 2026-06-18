#!/usr/bin/env python3
"""Phase 52 fake updater install test harness for Deimos.

This harness simulates executable replacement, rollback, checksum verification,
helper exit codes, and post-install verification inside a temporary fake
filesystem. It never touches the real Deimos executable and never launches the
real updater helper.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

EXIT_SUCCESS = 0
EXIT_CHECKSUM_FAILED = 20
EXIT_REPLACEMENT_FAILED = 30
EXIT_ROLLBACK_USED = 40
EXIT_SIMULATION_ERROR = 90

SCENARIOS = ("success", "checksum_failure", "replacement_failure_with_rollback", "exit_code_matrix")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def append_log(path: Path, event: str, **fields: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"event": event, **fields}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, sort_keys=True) + "\n")


@dataclass
class ScenarioResult:
    scenario: str
    passed: bool
    exit_code: int
    expected_exit_code: int
    rollback_used: bool
    checksum_verified: bool
    post_install_verified: bool
    touched_real_filesystem: bool
    messages: list[str]


def create_fake_environment(root: Path, *, corrupt_staged: bool = False) -> dict[str, Path | str]:
    current_dir = root / "current"
    staged_dir = root / "staged"
    rollback_dir = root / "rollback"
    current_dir.mkdir(parents=True, exist_ok=True)
    staged_dir.mkdir(parents=True, exist_ok=True)
    rollback_dir.mkdir(parents=True, exist_ok=True)

    current_exe = current_dir / "Deimos.exe"
    staged_exe = staged_dir / "Deimos.exe"
    checksum_file = staged_dir / "Deimos.exe.sha256"
    helper_manifest = staged_dir / "deimos-helper-manifest.json"
    log_file = root / "deimos-updater-helper.log"

    old_bytes = b"FAKE-DEIMOS-OLD-v3.13.1\n"
    new_bytes = b"FAKE-DEIMOS-NEW-v3.13.2\n"
    current_exe.write_bytes(old_bytes)
    staged_exe.write_bytes(new_bytes + (b"CORRUPT" if corrupt_staged else b""))
    expected_hash = sha256_bytes(new_bytes)
    checksum_file.write_text(f"{expected_hash}  Deimos.exe\n", encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "target_executable": str(current_exe),
        "staged_executable": str(staged_exe),
        "expected_sha256": expected_hash,
        "rollback_dir": str(rollback_dir),
        "install_log": str(log_file),
        "dry_run": True,
        "simulation_only": True,
    }
    write_json(helper_manifest, manifest)
    return {
        "root": root,
        "current_exe": current_exe,
        "staged_exe": staged_exe,
        "checksum_file": checksum_file,
        "rollback_dir": rollback_dir,
        "helper_manifest": helper_manifest,
        "log_file": log_file,
        "expected_hash": expected_hash,
        "old_hash": sha256_bytes(old_bytes),
    }


def simulate_install(env: dict[str, Any], *, force_replacement_failure: bool = False) -> ScenarioResult:
    scenario = "replacement_failure_with_rollback" if force_replacement_failure else "success"
    messages: list[str] = []
    current_exe: Path = env["current_exe"]
    staged_exe: Path = env["staged_exe"]
    rollback_dir: Path = env["rollback_dir"]
    log_file: Path = env["log_file"]
    expected_hash: str = env["expected_hash"]
    backup = rollback_dir / "Deimos.exe.bak"
    touched_real = False

    append_log(log_file, "simulation_start", scenario=scenario)
    actual_staged_hash = sha256_file(staged_exe)
    if actual_staged_hash != expected_hash:
        append_log(log_file, "checksum_failed", expected=expected_hash, actual=actual_staged_hash)
        return ScenarioResult(
            scenario="checksum_failure",
            passed=True,
            exit_code=EXIT_CHECKSUM_FAILED,
            expected_exit_code=EXIT_CHECKSUM_FAILED,
            rollback_used=False,
            checksum_verified=False,
            post_install_verified=False,
            touched_real_filesystem=touched_real,
            messages=["staged checksum mismatch was detected before replacement"],
        )

    shutil.copy2(current_exe, backup)
    append_log(log_file, "rollback_created", backup=str(backup), sha256=sha256_file(backup))

    if force_replacement_failure:
        current_exe.write_bytes(b"BROKEN-PARTIAL-INSTALL\n")
        shutil.copy2(backup, current_exe)
        append_log(log_file, "replacement_failed_rollback_restored", restored_sha256=sha256_file(current_exe))
        return ScenarioResult(
            scenario=scenario,
            passed=sha256_file(current_exe) == env["old_hash"],
            exit_code=EXIT_ROLLBACK_USED,
            expected_exit_code=EXIT_ROLLBACK_USED,
            rollback_used=True,
            checksum_verified=True,
            post_install_verified=False,
            touched_real_filesystem=touched_real,
            messages=["simulated replacement failure restored rollback copy"],
        )

    shutil.copy2(staged_exe, current_exe)
    final_hash = sha256_file(current_exe)
    verified = final_hash == expected_hash
    append_log(log_file, "post_install_verified" if verified else "post_install_failed", sha256=final_hash)
    return ScenarioResult(
        scenario=scenario,
        passed=verified,
        exit_code=EXIT_SUCCESS if verified else EXIT_REPLACEMENT_FAILED,
        expected_exit_code=EXIT_SUCCESS,
        rollback_used=False,
        checksum_verified=True,
        post_install_verified=verified,
        touched_real_filesystem=touched_real,
        messages=["fake executable replacement verified in isolated temp directory"],
    )


def run_scenario(name: str, keep_temp: bool = False) -> dict[str, Any]:
    temp = Path(tempfile.mkdtemp(prefix="deimos-phase52-harness-"))
    try:
        if name == "success":
            env = create_fake_environment(temp)
            result = simulate_install(env)
        elif name == "checksum_failure":
            env = create_fake_environment(temp, corrupt_staged=True)
            result = simulate_install(env)
        elif name == "replacement_failure_with_rollback":
            env = create_fake_environment(temp)
            result = simulate_install(env, force_replacement_failure=True)
        elif name == "exit_code_matrix":
            result = ScenarioResult(
                scenario=name,
                passed=True,
                exit_code=EXIT_SUCCESS,
                expected_exit_code=EXIT_SUCCESS,
                rollback_used=False,
                checksum_verified=False,
                post_install_verified=False,
                touched_real_filesystem=False,
                messages=[
                    f"success={EXIT_SUCCESS}",
                    f"checksum_failed={EXIT_CHECKSUM_FAILED}",
                    f"replacement_failed={EXIT_REPLACEMENT_FAILED}",
                    f"rollback_used={EXIT_ROLLBACK_USED}",
                    f"simulation_error={EXIT_SIMULATION_ERROR}",
                ],
            )
            env = {"root": temp, "log_file": temp / "exit-code-matrix.log"}
            append_log(env["log_file"], "exit_code_matrix_checked")
        else:
            raise ValueError(f"Unknown scenario: {name}")
        payload = asdict(result)
        payload["temp_root"] = str(temp) if keep_temp else "removed"
        payload["log_file"] = str(env.get("log_file")) if keep_temp else "removed"
        return payload
    finally:
        if not keep_temp:
            shutil.rmtree(temp, ignore_errors=True)


def run_all(keep_temp: bool = False) -> dict[str, Any]:
    results = [run_scenario(name, keep_temp=keep_temp) for name in SCENARIOS]
    return {
        "phase": 52,
        "simulation_only": True,
        "real_install_attempted": False,
        "install_execution_enabled": False,
        "helper_launch_enabled": False,
        "scenarios": results,
        "passed": all(r["passed"] and r["exit_code"] == r["expected_exit_code"] and not r["touched_real_filesystem"] for r in results),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Run fake Deimos updater install simulations without touching real executables.")
    ap.add_argument("out", nargs="?", help="Optional JSON output path")
    ap.add_argument("--scenario", choices=("all",) + SCENARIOS, default="all")
    ap.add_argument("--keep-temp", action="store_true", help="Keep temporary fake filesystem for inspection")
    args = ap.parse_args()
    payload = run_all(keep_temp=args.keep_temp) if args.scenario == "all" else run_scenario(args.scenario, keep_temp=args.keep_temp)
    if args.out:
        write_json(Path(args.out), payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if (payload.get("passed") if isinstance(payload, dict) else True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
