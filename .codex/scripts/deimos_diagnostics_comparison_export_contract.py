#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.update_system import (  # noqa: E402
    export_diagnostics_comparison_report_bundle,
    inspect_diagnostics_comparison_report_bundle,
)


def make_diag(path: Path, checksum: str, manifest: str, helper: str, blockers: int = 0) -> None:
    diagnostics = {
        "safe_bundle": True,
        "install_locked": True,
        "install_execution_enabled": False,
        "helper_launch_from_gui_enabled": False,
        "non_dry_run_enabled": False,
        "real_install_attempted": False,
        "summary": {
            "checksum_status": checksum,
            "manifest_status": manifest,
            "helper_log_status": helper,
            "problem_count": blockers,
            "blocker_count": blockers,
            "warning_count": 0,
            "install_locked": True,
            "install_execution_enabled": False,
            "helper_launch_from_gui_enabled": False,
            "non_dry_run_enabled": False,
            "real_install_attempted": False,
        },
    }
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.txt", "safe diagnostics")
        zf.writestr("deimos-staged-update-diagnostics.json", json.dumps(diagnostics))
        zf.writestr("artifacts/Deimos.exe.sha256", "0" * 64 + "  Deimos.exe\n")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        before = td / "before.zip"
        after = td / "after.zip"
        export_zip = td / "comparison-export.zip"
        make_diag(before, "verified", "valid", "missing", 0)
        make_diag(after, "verified", "valid", "valid", 0)
        export = export_diagnostics_comparison_report_bundle(before, after, export_zip)
        inspected = inspect_diagnostics_comparison_report_bundle(export_zip)
        with zipfile.ZipFile(export_zip) as zf:
            names = set(zf.namelist())
        checks = {
            "export_created": export_zip.exists(),
            "safe_bundle": export.get("safe_bundle") is True,
            "executable_payloads_excluded": export.get("executable_payloads_excluded") is True,
            "contains_required_files": {"README.txt", "comparison-review.json", "comparison-report.json", "source-summaries.json", "export-metadata.json"}.issubset(names),
            "excludes_executables": not any(Path(n).suffix.lower() == ".exe" for n in names),
            "inspect_valid": inspected.get("valid") is True,
            "install_locked": export.get("install_execution_enabled") is False and export.get("helper_launch_from_gui_enabled") is False,
        }
        unsafe = td / "unsafe.zip"
        shutil.copyfile(export_zip, unsafe)
        with zipfile.ZipFile(unsafe, "a", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("Deimos.exe", b"not allowed")
        unsafe_inspect = inspect_diagnostics_comparison_report_bundle(unsafe)
        checks["unsafe_executable_rejected"] = unsafe_inspect.get("valid") is False and unsafe_inspect.get("errors")
        result = {"phase": 65, "checks": checks, "passed": all(checks.values())}
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
