#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(args: list[str]) -> dict:
    proc = subprocess.run([sys.executable, *args], cwd=ROOT, text=True, capture_output=True)
    return {"args": args, "returncode": proc.returncode, "stdout": proc.stdout[-2000:], "stderr": proc.stderr[-2000:], "passed": proc.returncode == 0}


def has_function(path: Path, name: str) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return any(isinstance(n, ast.FunctionDef) and n.name == name for n in ast.walk(tree))


def main() -> int:
    compile_targets = [
        "src/update_system.py",
        "src/gui/update_check.py",
        ".codex/scripts/deimos_diagnostics_comparison_export.py",
        ".codex/scripts/deimos_diagnostics_comparison_export_contract.py",
        ".codex/scripts/deimos_diagnostics_comparison_export_smoke.py",
    ]
    checks = [run(["-m", "py_compile", *compile_targets])]
    checks.append(run([".codex/scripts/deimos_diagnostics_comparison_export_contract.py"]))
    checks.append(run([".codex/scripts/deimos_diagnostics_comparison_export_smoke.py"]))
    update_text = (ROOT / "src/update_system.py").read_text(encoding="utf-8")
    gui_text = (ROOT / "src/gui/update_check.py").read_text(encoding="utf-8")
    static = {
        "export_function_present": has_function(ROOT / "src/update_system.py", "export_diagnostics_comparison_report_bundle"),
        "inspect_function_present": has_function(ROOT / "src/update_system.py", "inspect_diagnostics_comparison_report_bundle"),
        "gui_export_path_present": "export_diagnostics_comparison_report_bundle" in gui_text and "getSaveFileName" in gui_text,
        "executable_exclusion_text_present": "executable_payloads_excluded" in update_text and "Deimos.exe" in update_text,
        "install_execution_locked": "install_execution_enabled\": False" in update_text or "'install_execution_enabled': False" in update_text,
        "helper_launch_locked": "helper_launch_from_gui_enabled\": False" in update_text or "'helper_launch_from_gui_enabled': False" in update_text,
    }
    result = {
        "phase": 65,
        "name": "diagnostics comparison export/share polish",
        "checks": checks,
        "static": static,
        "passed": all(c["passed"] for c in checks) and all(static.values()),
        "locks": {
            "diagnostics_comparison_export_read_only": True,
            "executable_payload_import": False,
            "helper_launch_from_gui_enabled": False,
            "install_execution_enabled": False,
            "non_dry_run_enabled": False,
            "real_install_attempted": False,
        },
        "blockers": [],
    }
    if not result["passed"]:
        result["blockers"].append("Phase 65 readiness checks failed")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
