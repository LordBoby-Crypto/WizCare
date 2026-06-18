#!/usr/bin/env python3
"""Report how Deimos bot editor GUI can integrate parser-aware validation.

Usage: python deimos_gui_bot_editor_integration_report.py <repo> [out.json]
"""
from __future__ import annotations
from pathlib import Path
import json, re, sys


def read(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8', errors='replace')
    except FileNotFoundError:
        return ''


def find_func_body(text: str, name: str) -> str:
    marker = f'def {name}('
    i = text.find(marker)
    if i < 0:
        return ''
    # naive top-level function slice for static reporting
    j = text.find('\ndef ', i + len(marker))
    return text[i:] if j < 0 else text[i:j]


def has_call(body: str, needle: str) -> bool:
    return needle in body


def main() -> int:
    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    gui = repo / 'src' / 'gui'
    tab_actions = read(gui / 'tab_actions.py')
    commands = read(gui / 'commands.py')
    main_py = read(gui / 'main.py')
    helpers = read(gui / 'helpers.py')
    popups = read(gui / 'popups.py')

    bot_body = find_func_body(tab_actions, 'build_bot_tab')
    integration_points = {
        'bot_tab_function_found': bool(bot_body),
        'editor_widget_tag_bot_creator': "ctx.widget_tags['bot_creator']" in bot_body or 'ctx.widget_tags["bot_creator"]' in bot_body,
        'import_callback_reads_text': 'bot_import' in bot_body and 'setPlainText' in bot_body,
        'export_callback_writes_text': 'bot_export' in bot_body and 'toPlainText' in bot_body,
        'run_callback_sends_execute_bot': 'GUICommandType.ExecuteBot' in bot_body and 'editor.toPlainText()' in bot_body,
        'kill_callback_sends_kill_bot': 'GUICommandType.KillBot' in bot_body,
        'recent_imports_menu_connected': 'show_recent_menu' in bot_body,
        'commands_execute_bot_enum': 'ExecuteBot' in commands,
        'commands_kill_bot_enum': 'KillBot' in commands,
        'main_handles_bot_export_state': 'set_running' in main_py and 'bot_exports' in main_py,
    }

    recommended_hook = {
        'file': 'src/gui/tab_actions.py',
        'function': 'build_bot_tab',
        'recommended_behavior': [
            'Before GUICommandType.ExecuteBot is queued, run a lightweight validator on editor.toPlainText().',
            'If validation has errors, show a localized message and do not queue ExecuteBot.',
            'If validation has warnings only, allow run only after explicit user confirmation.',
            'Validation should be pure/static and must not execute bot code or connect to the game client.',
            'Import/export should not mutate bot content except optional newline normalization.'
        ],
        'minimal_patch_shape': [
            'Add helper function validate_bot_text_for_gui(ctx, text).',
            'Call the helper inside run_bot_callback before ctx.send_queue.put(...).',
            'Use ctx.tl(...) for every user-visible label/message.',
            'Keep validation optional/fail-closed only for parser errors, not for unknown Wizard101 knowledge links.'
        ]
    }

    required_locale_keys = [
        'validate_bot', 'bot_validation_title', 'bot_validation_errors',
        'bot_validation_warnings', 'bot_validation_run_anyway',
        'bot_validation_cancelled', 'bot_validation_no_issues',
        'bot_validation_unknown_command', 'bot_validation_bad_arguments',
        'bot_validation_bad_coordinate', 'bot_validation_bad_selector',
        'bot_validation_unknown_zone', 'bot_validation_missing_combat_marker'
    ]

    report = {
        'repo': str(repo),
        'phase': 27,
        'focus': 'gui bot-editor validator integration',
        'integration_points': integration_points,
        'all_required_current_surfaces_found': all(integration_points.values()),
        'recommended_hook': recommended_hook,
        'required_locale_keys_for_future_patch': required_locale_keys,
        'risk_notes': [
            'Do not add blocking GUI validation that rejects legacy bot scripts solely because Wizard101 knowledge data is incomplete.',
            'Do not execute imported bot files during validation.',
            'Do not add user-visible strings without updating locale/en.lang and locale/zh.lang together.',
            'Keep parser validation separate from strategy/meta validation.'
        ],
        'source_files_checked': [
            'src/gui/tab_actions.py', 'src/gui/commands.py', 'src/gui/main.py',
            'src/gui/helpers.py', 'src/gui/popups.py'
        ]
    }
    text = json.dumps(report, indent=2, sort_keys=True)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + '\n', encoding='utf-8')
    else:
        print(text)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
