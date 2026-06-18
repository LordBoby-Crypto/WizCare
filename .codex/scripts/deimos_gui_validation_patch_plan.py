#!/usr/bin/env python3
"""Create a conservative patch plan for GUI bot validation integration.

Usage: python deimos_gui_validation_patch_plan.py <repo> [out.md]
"""
from __future__ import annotations
from pathlib import Path
import json, sys


def file_has(path: Path, text: str) -> bool:
    try:
        return text in path.read_text(encoding='utf-8', errors='replace')
    except FileNotFoundError:
        return False


def main() -> int:
    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    checks = {
        'tab_actions_build_bot_tab': file_has(repo / 'src/gui/tab_actions.py', 'def build_bot_tab'),
        'execute_bot_command_exists': file_has(repo / 'src/gui/commands.py', 'ExecuteBot'),
        'locale_en_exists': (repo / 'locale/en.lang').exists(),
        'locale_zh_exists': (repo / 'locale/zh.lang').exists(),
        'command_parser_exists': (repo / 'src/command_parser.py').exists(),
        'deimoslang_package_exists': (repo / 'src/deimoslang').exists(),
    }
    md = []
    md.append('# Phase 27 GUI Bot Validation Patch Plan')
    md.append('')
    md.append('## Static readiness')
    for k, v in checks.items():
        md.append(f'- {k}: {str(v).lower()}')
    md.append('')
    md.append('## Recommended patch sequence')
    md.extend([
        '1. Add a pure static validator helper for bot text. Prefer a small module such as `src/gui/bot_validation.py` or a local helper in `src/gui/tab_actions.py`.',
        '2. In `build_bot_tab`, call the validator inside `run_bot_callback` before queuing `GUICommandType.ExecuteBot`.',
        '3. Blocking parser errors should prevent execution. Warnings should show a localized confirmation prompt.',
        '4. Add localized keys to `locale/en.lang` and `locale/zh.lang` at the same time.',
        '5. Do not change the `ExecuteBot` payload shape unless backend command handling is updated and reviewed.',
        '6. Run parser-aware validation, locale checks, and command-surface reports after the patch.'
    ])
    md.append('')
    md.append('## Minimum commands to run after patch')
    md.extend([
        '- `python .codex/scripts/deimos_parser_aware_bot_validator.py . .codex/reports/parser_aware_bot_validation.json`',
        '- `python .codex/scripts/deimos_gui_validation_message_contract.py . .codex/reports/gui_validation_messages.json`',
        '- `python .codex/scripts/deimos_gui_command_surface_guardrail.py . .codex/reports/gui_command_surface.json`',
        '- `python .codex/scripts/deimos_gui_bot_editor_integration_report.py . .codex/reports/gui_bot_editor_integration.json`'
    ])
    md.append('')
    md.append('## Hard blockers')
    md.extend([
        '- Do not execute bot text during validation.',
        '- Do not reject legacy scripts because Wizard101 knowledge coverage is incomplete.',
        '- Do not add English-only GUI text.',
        '- Do not route invalid bot scripts into the backend execution path.'
    ])
    text = '\n'.join(md) + '\n'
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding='utf-8')
    else:
        print(text)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
