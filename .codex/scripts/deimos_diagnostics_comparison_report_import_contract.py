#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.update_system import (  # noqa: E402
    STAGED_DIAGNOSTICS_COMPARISON_REPORT_IMPORT_REVIEW_VERSION,
    build_diagnostics_comparison_report_import_review,
)


def write_safe_bundle(path: Path) -> None:
    review = {
        "severity": "warning",
        "headline": "1 staged-update state changed.",
        "difference_count": 1,
        "blocker_count": 0,
        "warning_count": 1,
        "rows": [{"label": "helper_log_status", "before": "missing", "after": "valid", "severity": "warning"}],
        "next_steps": ["Review the newer helper dry-run log."],
    }
    metadata = {
        "version": "phase65-diagnostics-comparison-export-v1",
        "safe_bundle": True,
        "executable_payloads_excluded": True,
        "review_only": True,
    }
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.txt", "safe comparison export\n")
        zf.writestr("comparison-review.json", json.dumps(review))
        zf.writestr("comparison-report.json", json.dumps({"differences": review["rows"]}))
        zf.writestr("source-summaries.json", json.dumps({"before": {}, "after": {}}))
        zf.writestr("export-metadata.json", json.dumps(metadata))


def write_unsafe_bundle(path: Path) -> None:
    write_safe_bundle(path)
    with zipfile.ZipFile(path, "a", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("Deimos.exe", b"not allowed")


def main() -> int:
    tmp = ROOT / ".codex" / "reports" / "phase67-contract"
    tmp.mkdir(parents=True, exist_ok=True)
    safe = tmp / "safe-comparison-export.zip"
    unsafe = tmp / "unsafe-comparison-export.zip"
    write_safe_bundle(safe)
    write_unsafe_bundle(unsafe)

    safe_review = build_diagnostics_comparison_report_import_review(safe)
    unsafe_review = build_diagnostics_comparison_report_import_review(unsafe)
    blockers: list[str] = []
    if safe_review.get("version") != STAGED_DIAGNOSTICS_COMPARISON_REPORT_IMPORT_REVIEW_VERSION:
        blockers.append("wrong import-review version")
    if not safe_review.get("valid") or not safe_review.get("safe_bundle"):
        blockers.append("safe bundle did not import as valid/safe")
    if safe_review.get("status") != "valid":
        blockers.append("safe bundle status was not valid")
    if safe_review.get("executable_payloads_excluded") is not True:
        blockers.append("safe bundle did not preserve executable exclusion flag")
    if unsafe_review.get("valid") or unsafe_review.get("safe_bundle"):
        blockers.append("unsafe executable payload bundle was not rejected")
    for key in ["install_execution_enabled", "helper_launch_from_gui_enabled", "non_dry_run_enabled", "real_install_attempted"]:
        if safe_review.get(key) is not False:
            blockers.append(f"{key} must remain false")
    report = {
        "phase": 67,
        "name": "diagnostics-comparison-exported-report-import-review-contract",
        "passed": not blockers,
        "blockers": blockers,
        "safe_review": safe_review,
        "unsafe_status": unsafe_review.get("status"),
        "unsafe_errors": unsafe_review.get("errors"),
    }
    out = ROOT / ".codex" / "reports" / "phase67-diagnostics-comparison-report-import-contract.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
