#!/usr/bin/env python3
from __future__ import annotations
import json, sys, tempfile, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.update_system import build_diagnostics_comparison_report_import_review, build_diagnostics_comparison_report_import_gui_summary


def write_bundle(path: Path, unsafe: bool = False, malformed: bool = False) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.txt", "Deimos diagnostics comparison export. Executables are excluded.\n")
        zf.writestr("comparison-review.json", "{" if malformed else json.dumps({
            "headline": "Diagnostics comparison has tracked changes.",
            "severity": "warning",
            "difference_count": 2,
            "blocker_count": 0,
            "warning_count": 1,
            "rows": [{"label":"checksum_status", "before":"missing", "after":"verified", "severity":"info"}],
            "next_steps": ["Review the staged update diagnostics."],
        }))
        zf.writestr("comparison-report.json", json.dumps({"differences": []}))
        zf.writestr("source-summaries.json", json.dumps({"before": {}, "after": {}}))
        zf.writestr("export-metadata.json", json.dumps({
            "version": "phase65-diagnostics-comparison-export-v1",
            "safe_bundle": True,
            "executable_payloads_excluded": True,
        }))
        if unsafe:
            zf.writestr("Deimos.exe", b"not allowed")

def main() -> int:
    report = {"phase": 68, "name": "diagnostics-report-import-gui-smoke", "scenarios": [], "blockers": []}
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        safe = td / "safe.zip"; write_bundle(safe)
        unsafe = td / "unsafe.zip"; write_bundle(unsafe, unsafe=True)
        bad = td / "malformed.zip"; write_bundle(bad, malformed=True)
        scenarios = [("safe", safe, True), ("unsafe", unsafe, False), ("malformed", bad, False)]
        for name, path, expected_valid in scenarios:
            review = build_diagnostics_comparison_report_import_review(path)
            summary = build_diagnostics_comparison_report_import_gui_summary(review)
            passed = bool(summary["review_only"] and not summary["install_execution_enabled"] and not summary["helper_launch_from_gui_enabled"] and summary["valid"] == expected_valid)
            if name != "safe":
                passed = passed and bool(summary["errors"])
            report["scenarios"].append({"name": name, "passed": passed, "valid": summary["valid"], "status": summary["status"], "errors": summary["errors"]})
            if not passed:
                report["blockers"].append(f"scenario failed: {name}")
    out = ROOT / ".codex/reports/phase68-diagnostics-report-import-gui-smoke.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["blockers"] else 0
if __name__ == "__main__":
    raise SystemExit(main())
