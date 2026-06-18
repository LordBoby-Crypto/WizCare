#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
REQUIRED_UPDATE_SYSTEM = [
    "build_diagnostics_comparison_report_import_gui_summary",
    "STAGED_DIAGNOSTICS_COMPARISON_REPORT_IMPORT_GUI_VERSION",
    "diagnostics_report_import_read_only",
    "executable_payload_import",
    "install_execution_enabled",
]
REQUIRED_GUI = [
    "show_diagnostics_comparison_report_import_dialog",
    "_format_diagnostics_comparison_report_import_text",
    "build_diagnostics_comparison_report_import_review",
    "build_diagnostics_comparison_report_import_gui_summary",
    "Review only: no executables are imported",
]
REQUIRED_TAB = [
    "show_diagnostics_comparison_report_import_dialog",
    "import_diagnostics_comparison_report",
    "tooltip_import_diagnostics_comparison_report",
]
REQUIRED_LOCALE = [
    "update_diagnostics_report_import=",
    "update_diagnostics_report_import_title=",
    "update_diagnostics_report_import_locked=",
    "tooltip_import_diagnostics_comparison_report=",
]

def missing(text: str, values: list[str]) -> list[str]:
    return [v for v in values if v not in text]

def main() -> int:
    report = {"phase": 68, "name": "diagnostics-report-import-gui-contract", "checks": [], "blockers": []}
    files = {
        "update_system": ROOT / "src/update_system.py",
        "update_check": ROOT / "src/gui/update_check.py",
        "tab_hotkeys": ROOT / "src/gui/tab_hotkeys.py",
        "locale_en": ROOT / "locale/en.lang",
        "locale_zh": ROOT / "locale/zh.lang",
    }
    for label, path in files.items():
        text = path.read_text(encoding="utf-8")
        values = REQUIRED_UPDATE_SYSTEM if label == "update_system" else REQUIRED_GUI if label == "update_check" else REQUIRED_TAB if label == "tab_hotkeys" else REQUIRED_LOCALE
        misses = missing(text, values)
        report["checks"].append({"file": label, "path": str(path), "passed": not misses, "missing": misses})
        report["blockers"].extend(f"{label}: missing {m}" for m in misses)
    out = ROOT / ".codex/reports/phase68-diagnostics-report-import-gui-contract.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["blockers"] else 0
if __name__ == "__main__":
    raise SystemExit(main())
