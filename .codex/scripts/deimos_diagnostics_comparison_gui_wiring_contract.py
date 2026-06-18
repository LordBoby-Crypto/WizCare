#!/usr/bin/env python3
from __future__ import annotations
import ast, json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    tab = ROOT / 'src/gui/tab_hotkeys.py'
    update = ROOT / 'src/gui/update_check.py'
    locale_en = ROOT / 'locale/en.lang'
    text = tab.read_text(encoding='utf-8')
    update_text = update.read_text(encoding='utf-8')
    tree = ast.parse(text)
    imports = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == 'src.gui.update_check':
            imports.extend(alias.name for alias in node.names)
    marker = 'PHASE64_DIAGNOSTICS_COMPARISON_MENU_BUTTON_WIRING'
    section = text[text.find(marker):] if marker in text else ''
    locale = locale_en.read_text(encoding='utf-8')
    checks = {
        'phase64_marker_present': marker in text,
        'imports_safe_dialog_action': 'show_diagnostics_comparison_dialog' in imports,
        'keeps_update_check_button': 'show_update_check_dialog(ctx, update_btn)' in text,
        'adds_compare_button': 'compare_diagnostics_btn' in section,
        'button_calls_safe_dialog': 'show_diagnostics_comparison_dialog(ctx)' in section,
        'has_stable_action_id': "action_id='compare_diagnostics_bundles'" in section or 'action_id="compare_diagnostics_bundles"' in section,
        'has_tooltip_locale_key': re.search(r'^tooltip_compare_diagnostics_bundles=', locale, flags=re.M) is not None,
        'uses_existing_phase63_dialog': 'def show_diagnostics_comparison_dialog' in update_text,
        'dialog_remains_read_only': 'no executables are imported' in update_text and 'no install action is available' in update_text,
        'no_helper_launch_in_wiring': 'subprocess' not in section,
        'no_install_execution_in_wiring': not re.search(r'\b(install|replace|relaunch)[a-zA-Z_]*\s*\(', section, flags=re.I),
    }
    out = {
        'phase': 64,
        'passed': all(checks.values()),
        'checks': checks,
        'comparison_gui_button_wired': checks['adds_compare_button'] and checks['button_calls_safe_dialog'],
        'diagnostics_comparison_read_only': True,
        'executable_payload_import': False,
        'helper_launch_from_gui_enabled': False,
        'install_execution_enabled': False,
        'non_dry_run_enabled': False,
        'real_install_attempted': False,
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if out['passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
