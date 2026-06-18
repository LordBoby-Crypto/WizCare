#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
REQUIRED_UPDATE_CHECK = [
    "DIAGNOSTICS_REPORT_IMPORT_GUI_WIRING_VERSION",
    "build_diagnostics_report_import_gui_wiring_metadata",
    "update_diagnostics_report_import_button_safety",
    "diagnostics_report_import_read_only",
    "executable_payload_import",
    "install_execution_enabled",
    "helper_launch_from_gui_enabled",
]
REQUIRED_TAB = [
    "build_diagnostics_report_import_gui_wiring_metadata",
    "import_report_wiring[\"action_id\"]",
    "import_report_wiring['safety_note']",
    "import_diagnostics_report_note",
]
REQUIRED_LOCALE = [
    "update_diagnostics_report_import_button_safety=",
]


def missing(text: str, values: list[str]) -> list[str]:
    return [v for v in values if v not in text]


def main() -> int:
    report = {"phase": 69, "name": "diagnostics-report-import-gui-wiring-contract", "checks": [], "blockers": []}
    files = {
        "update_check": (ROOT / "src/gui/update_check.py", REQUIRED_UPDATE_CHECK),
        "tab_hotkeys": (ROOT / "src/gui/tab_hotkeys.py", REQUIRED_TAB),
        "locale_en": (ROOT / "locale/en.lang", REQUIRED_LOCALE),
        "locale_zh": (ROOT / "locale/zh.lang", REQUIRED_LOCALE),
    }
    for label, (path, values) in files.items():
        text = path.read_text(encoding="utf-8")
        misses = missing(text, values)
        report["checks"].append({"file": label, "path": str(path), "passed": not misses, "missing": misses})
        report["blockers"].extend(f"{label}: missing {m}" for m in misses)
    out = ROOT / ".codex/reports/phase69-diagnostics-report-import-gui-wiring-contract.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
