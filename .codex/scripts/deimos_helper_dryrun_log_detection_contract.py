#!/usr/bin/env python3
"""Phase 56 contract check for staged helper dry-run log detection."""
from __future__ import annotations
import json
import sys
from pathlib import Path


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else root / ".codex" / "reports" / "phase56-helper-log-detection-contract.json"
    update_system = root / "src" / "update_system.py"
    update_gui = root / "src" / "gui" / "update_check.py"
    en = root / "locale" / "en.lang"
    zh = root / "locale" / "zh.lang"
    blockers: list[str] = []
    required_update_tokens = [
        "HELPER_DRY_RUN_REQUIRED_EVENTS",
        "classify_helper_dry_run_log",
        "helper_log_valid",
        "helper_log_missing_events",
        "helper_log_invalid_entries",
        "helper_log_message",
    ]
    required_gui_tokens = [
        "update_helper_dry_run_log_status",
        "update_helper_dry_run_missing_events",
        "update_helper_dry_run_invalid_entries",
        "helper_log_missing_events",
        "helper_log_invalid_entries",
    ]
    utext = update_system.read_text(encoding="utf-8") if update_system.exists() else ""
    gtext = update_gui.read_text(encoding="utf-8") if update_gui.exists() else ""
    for token in required_update_tokens:
        if token not in utext:
            blockers.append(f"src/update_system.py missing token: {token}")
    for token in required_gui_tokens:
        if token not in gtext:
            blockers.append(f"src/gui/update_check.py missing token: {token}")
    locale_keys = [
        "update_helper_dry_run_log_status",
        "update_helper_dry_run_missing_events",
        "update_helper_dry_run_invalid_entries",
    ]
    for path in (en, zh):
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        for key in locale_keys:
            if f"{key}=" not in text:
                blockers.append(f"{path.relative_to(root)} missing locale key: {key}")
    report = {
        "phase": 56,
        "name": "helper dry-run staged-log detection contract",
        "passed": not blockers,
        "blockers": blockers,
        "install_execution_enabled": False,
        "helper_launch_from_gui_enabled": False,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not blockers else 1

if __name__ == "__main__":
    raise SystemExit(main())
