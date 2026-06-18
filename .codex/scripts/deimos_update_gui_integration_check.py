#!/usr/bin/env python3
"""Check that the manual update-check GUI is wired safely."""
from __future__ import annotations
import json
import sys
from pathlib import Path

REQUIRED_LOCALE_KEYS = [
    "check_for_updates",
    "tooltip_check_for_updates",
    "update_checking",
    "update_available_title",
    "update_available_message",
    "update_not_available_title",
    "update_not_available_message",
    "update_error_title",
    "update_error_message",
    "update_open_release",
    "update_unknown_version",
    "update_asset_contract",
    "update_install_locked",
    "update_warnings_header",
]


def read_keys(path: Path) -> dict[str, str]:
    out = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    tab = root / "src/gui/tab_hotkeys.py"
    module = root / "src/gui/update_check.py"
    update_system = root / "src/update_system.py"
    en = read_keys(root / "locale/en.lang")
    zh = read_keys(root / "locale/zh.lang")
    tab_text = tab.read_text(encoding="utf-8", errors="replace") if tab.exists() else ""
    mod_text = module.read_text(encoding="utf-8", errors="replace") if module.exists() else ""

    checks = {
        "update_check_module_present": module.exists(),
        "update_system_present": update_system.exists(),
        "tab_imports_update_check": "from src.gui.update_check import show_update_check_dialog" in tab_text,
        "check_button_present": "check_for_updates" in tab_text and "show_update_check_dialog" in tab_text,
        "manual_install_locked": "does not install" in mod_text or "disabled" in mod_text,
        "uses_qthread": "QThread" in mod_text,
        "locale_en_missing": [k for k in REQUIRED_LOCALE_KEYS if k not in en],
        "locale_zh_missing": [k for k in REQUIRED_LOCALE_KEYS if k not in zh],
    }
    blockers = []
    for key in ("update_check_module_present", "update_system_present", "tab_imports_update_check", "check_button_present", "manual_install_locked", "uses_qthread"):
        if not checks[key]:
            blockers.append(key)
    if checks["locale_en_missing"]:
        blockers.append("locale_en_missing")
    if checks["locale_zh_missing"]:
        blockers.append("locale_zh_missing")
    report = {"checks": checks, "blockers": blockers, "passed": not blockers}
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    else:
        print(json.dumps(report, indent=2))
    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
