#!/usr/bin/env python3
"""Validate Phase 28 GUI bot-validation patch files against a Deimos repo."""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

REQUIRED_KEYS = [
    "bot_validation_failed_title",
    "bot_validation_warning_title",
    "bot_validation_run_anyway",
    "bot_validation_empty_script",
    "bot_validation_no_actions",
    "bot_validation_unknown_command",
    "bot_validation_bad_client_selector",
    "bot_validation_missing_zone",
    "bot_validation_negative_wait",
    "bot_validation_long_wait",
    "bot_validation_combat_marker_client_range",
    "bot_validation_combat_without_client_metadata",
    "bot_validation_passed",
]

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    repo = args.repo
    report = {"ok": True, "errors": [], "warnings": [], "checks": {}}

    bot_validation = repo / "src/gui/bot_validation.py"
    tab_actions = repo / "src/gui/tab_actions.py"
    en = repo / "locale/en.lang"
    zh = repo / "locale/zh.lang"

    report["checks"]["bot_validation_exists"] = bot_validation.exists()
    report["checks"]["tab_actions_exists"] = tab_actions.exists()
    if not bot_validation.exists():
        report["errors"].append("src/gui/bot_validation.py is missing")
    if not tab_actions.exists():
        report["errors"].append("src/gui/tab_actions.py is missing")

    tab_text = read(tab_actions)
    report["checks"]["imports_validate_bot_script"] = "validate_bot_script" in tab_text
    report["checks"]["imports_qmessagebox"] = "QMessageBox" in tab_text
    report["checks"]["execute_bot_still_queued"] = "GUICommandType.ExecuteBot" in tab_text
    if tab_actions.exists() and "validate_bot_script" not in tab_text:
        report["errors"].append("tab_actions.py does not call validate_bot_script")
    if tab_actions.exists() and "QMessageBox" not in tab_text:
        report["warnings"].append("tab_actions.py does not use QMessageBox for validation feedback")

    for name, path in [("en", en), ("zh", zh)]:
        text = read(path)
        keys = {line.split("=",1)[0].strip() for line in text.splitlines() if "=" in line and not line.lstrip().startswith("#")}
        missing = [key for key in REQUIRED_KEYS if key not in keys]
        report["checks"][f"{name}_missing_keys"] = missing
        if missing:
            report["errors"].append(f"locale/{name}.lang missing keys: {', '.join(missing)}")

    report["ok"] = not report["errors"]
    output = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0 if report["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
