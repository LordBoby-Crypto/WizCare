#!/usr/bin/env python3
from __future__ import annotations
import json, sys, zipfile, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.update_system import import_staged_update_diagnostics_bundle, compare_staged_update_diagnostics_bundles, STAGED_DIAGNOSTICS_FILENAME

def write_bundle(path: Path, checksum="verified", manifest="valid", helper="valid", blockers=0, unsafe=False):
    diag = {
        "review_only": True,
        "install_locked": True,
        "install_execution_enabled": False,
        "helper_launch_from_gui_enabled": False,
        "non_dry_run_enabled": False,
        "real_install_attempted": False,
        "summary": {
            "headline": "test bundle",
            "checksum_status": checksum,
            "manifest_status": manifest,
            "helper_log_status": helper,
            "problem_count": blockers,
            "blocker_count": blockers,
            "warning_count": 0,
            "install_locked": True,
        },
    }
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(STAGED_DIAGNOSTICS_FILENAME, json.dumps(diag))
        zf.writestr("README.txt", "safe diagnostics")
        zf.writestr("artifacts/Deimos.exe.sha256", "abc  Deimos.exe\n")
        if unsafe:
            zf.writestr("artifacts/Deimos.exe", "not allowed")

def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        a = td/"a.zip"; b = td/"b.zip"; unsafe = td/"unsafe.zip"
        write_bundle(a)
        write_bundle(b, checksum="mismatch", helper="incomplete", blockers=1)
        write_bundle(unsafe, unsafe=True)
        imported = import_staged_update_diagnostics_bundle(a)
        unsafe_import = import_staged_update_diagnostics_bundle(unsafe)
        comparison = compare_staged_update_diagnostics_bundles(a, b)
        checks = {
            "safe_import_valid": imported.get("valid") is True,
            "unsafe_executable_rejected": unsafe_import.get("valid") is False and "diagnostics_bundle_contains_executable_payload" in unsafe_import.get("errors", []),
            "comparison_valid": comparison.get("valid") is True,
            "comparison_detects_checksum": "checksum_status" in comparison.get("changed_fields", []),
            "comparison_detects_helper": "helper_log_status" in comparison.get("changed_fields", []),
            "comparison_is_read_only": comparison.get("install_execution_enabled") is False and comparison.get("real_install_attempted") is False,
        }
    print(json.dumps({"passed": all(checks.values()), "checks": checks}, indent=2, sort_keys=True))
    return 0 if all(checks.values()) else 1
if __name__ == "__main__":
    raise SystemExit(main())
