#!/usr/bin/env python3
from __future__ import annotations
import ast, json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def main() -> int:
    gui = ROOT/'src/gui/update_check.py'
    text = gui.read_text(encoding='utf-8')
    tree = ast.parse(text)
    functions = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    locale = (ROOT/'locale/en.lang').read_text(encoding='utf-8')
    required_keys = [
        'update_diagnostics_compare_title',
        'update_diagnostics_compare_locked',
        'update_diagnostics_compare_headline',
        'update_diagnostics_compare_severity',
        'update_diagnostics_compare_choose_before',
        'update_diagnostics_compare_choose_after',
        'update_diagnostics_compare_failed_title',
        'update_diagnostics_compare_failed_message',
    ]
    checks = {
        'has_dialog_function': 'show_diagnostics_comparison_dialog' in functions,
        'has_formatter_function': '_format_diagnostics_comparison_review_text' in functions,
        'imports_review_comparator': 'compare_staged_update_diagnostics_bundles_for_review' in text,
        'uses_two_zip_open_dialogs': text.count('QFileDialog.getOpenFileName') >= 2,
        'uses_read_only_review_builder': 'compare_staged_update_diagnostics_bundles_for_review(before, after)' in text,
        'no_helper_launch': 'subprocess' not in text[text.find('PHASE63_DIAGNOSTICS_COMPARISON_GUI_ACTION_SCAFFOLD'):],
        'no_install_call': 'install' not in ' '.join(re.findall(r'\b[a-zA-Z_]*install[a-zA-Z_]*\s*\(', text[text.find('PHASE63_DIAGNOSTICS_COMPARISON_GUI_ACTION_SCAFFOLD'):], flags=re.I)),
        'locale_keys_present': all(re.search(rf'^{re.escape(k)}=', locale, flags=re.M) for k in required_keys),
        'read_only_text_present': 'no executables are imported' in text and 'no install action is available' in text,
    }
    out={
        'phase': 63,
        'passed': all(checks.values()),
        'checks': checks,
        'helper_launch_from_gui_enabled': False,
        'install_execution_enabled': False,
        'non_dry_run_enabled': False,
        'real_install_attempted': False,
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if out['passed'] else 1
if __name__=='__main__':
    raise SystemExit(main())
