#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.update_system import build_diagnostics_comparison_report_import_review  # noqa: E402


def make_bundle(path: Path, *, missing: bool = False, malformed: bool = False) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.txt", "comparison export\n")
        if not missing:
            zf.writestr("comparison-review.json", "{" if malformed else json.dumps({"severity": "ok", "headline": "No differences.", "difference_count": 0}))
            zf.writestr("comparison-report.json", json.dumps({"differences": []}))
            zf.writestr("source-summaries.json", json.dumps({"before": {}, "after": {}}))
            zf.writestr("export-metadata.json", json.dumps({"safe_bundle": True, "executable_payloads_excluded": True}))


def main() -> int:
    tmp = ROOT / ".codex" / "reports" / "phase67-smoke"
    tmp.mkdir(parents=True, exist_ok=True)
    valid = tmp / "valid.zip"
    missing = tmp / "missing.zip"
    malformed = tmp / "malformed.zip"
    make_bundle(valid)
    make_bundle(missing, missing=True)
    make_bundle(malformed, malformed=True)

    cases = {
        "valid": build_diagnostics_comparison_report_import_review(valid),
        "missing": build_diagnostics_comparison_report_import_review(missing),
        "malformed": build_diagnostics_comparison_report_import_review(malformed),
    }
    blockers = []
    if cases["valid"].get("status") != "valid":
        blockers.append("valid exported comparison report did not import as valid")
    if cases["missing"].get("status") == "valid":
        blockers.append("missing-file comparison report imported as valid")
    if cases["malformed"].get("status") == "valid":
        blockers.append("malformed comparison report imported as valid")
    report = {
        "phase": 67,
        "name": "diagnostics-comparison-exported-report-import-review-smoke",
        "passed": not blockers,
        "blockers": blockers,
        "case_statuses": {k: v.get("status") for k, v in cases.items()},
        "case_errors": {k: v.get("errors") for k, v in cases.items()},
        "install_execution_enabled": False,
        "helper_launch_from_gui_enabled": False,
        "non_dry_run_enabled": False,
        "real_install_attempted": False,
    }
    out = ROOT / ".codex" / "reports" / "phase67-diagnostics-comparison-report-import-smoke.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
