#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.update_system import build_diagnostics_comparison_export_gui_summary, diagnostics_comparison_export_default_filename


def main() -> int:
    review = {"severity": "warning", "difference_count": 3, "blocker_count": 0, "warning_count": 1}
    export = {"safe_bundle": True, "executable_payloads_excluded": True, "files": ["README.txt", "comparison-review.json"], "output_zip": "out.zip"}
    summary = build_diagnostics_comparison_export_gui_summary(review, export, "out.zip")
    blockers = []
    if summary.get("status") != "saved": blockers.append("saved export summary did not report saved")
    if summary.get("default_filename") != "deimos-diagnostics-comparison-warning-3-changes.zip": blockers.append("default filename is not severity/difference based")
    if summary.get("install_execution_enabled") is not False: blockers.append("install execution flag must stay false")
    if summary.get("helper_launch_from_gui_enabled") is not False: blockers.append("helper GUI launch flag must stay false")
    if summary.get("executable_payloads_excluded") is not True: blockers.append("export summary must show executable payload exclusion")
    failed = build_diagnostics_comparison_export_gui_summary(review, {}, None, "boom")
    if failed.get("status") != "failed": blockers.append("failure summary did not report failed")
    report = {"phase": 66, "contract": "diagnostics-comparison-export-gui", "passed": not blockers, "blockers": blockers, "summary": summary, "failure_summary": failed}
    out = ROOT/'.codex/reports/phase66-diagnostics-comparison-export-gui-contract.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not blockers else 1

if __name__ == '__main__':
    raise SystemExit(main())
