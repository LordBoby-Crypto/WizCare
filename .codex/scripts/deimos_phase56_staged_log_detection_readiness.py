#!/usr/bin/env python3
"""Aggregate Phase 56 staged helper dry-run log detection readiness."""
from __future__ import annotations
import json
import py_compile
import subprocess
import sys
from pathlib import Path


def run_py(root: Path, script: str, report_name: str) -> tuple[bool, dict]:
    out = root / ".codex" / "reports" / report_name
    proc = subprocess.run([sys.executable, str(root / ".codex" / "scripts" / script), str(root), str(out)], text=True, capture_output=True)
    data = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {"blockers": [proc.stderr or proc.stdout]}
    return proc.returncode == 0, data


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else root / ".codex" / "reports" / "phase56-staged-log-detection-readiness.json"
    blockers: list[str] = []
    compiled = []
    for rel in ["src/update_system.py", "src/gui/update_check.py"]:
        try:
            py_compile.compile(str(root / rel), doraise=True)
            compiled.append(rel)
        except py_compile.PyCompileError as exc:
            blockers.append(f"compile failed for {rel}: {exc}")
    for script in [
        "deimos_helper_dryrun_log_detection_contract.py",
        "deimos_helper_dryrun_log_detection_smoke.py",
    ]:
        try:
            py_compile.compile(str(root / ".codex" / "scripts" / script), doraise=True)
            compiled.append(f".codex/scripts/{script}")
        except py_compile.PyCompileError as exc:
            blockers.append(f"compile failed for {script}: {exc}")
    contract_ok, contract = run_py(root, "deimos_helper_dryrun_log_detection_contract.py", "phase56-contract.json")
    smoke_ok, smoke = run_py(root, "deimos_helper_dryrun_log_detection_smoke.py", "phase56-smoke.json")
    if not contract_ok:
        blockers.extend(f"contract: {b}" for b in contract.get("blockers", []))
    if not smoke_ok:
        blockers.extend(f"smoke: {b}" for b in smoke.get("blockers", []))
    report = {
        "phase": 56,
        "name": "GUI staged helper dry-run log detection polish",
        "passed": not blockers,
        "compiled": compiled,
        "contract": contract,
        "smoke": smoke,
        "blockers": blockers,
        "install_execution_enabled": False,
        "helper_launch_from_gui_enabled": False,
        "non_dry_run_enabled": False,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not blockers else 1

if __name__ == "__main__":
    raise SystemExit(main())
