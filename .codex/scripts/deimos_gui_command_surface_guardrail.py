#!/usr/bin/env python3
"""Inspect GUI command surfaces relevant to bot validation integration.

Usage: python deimos_gui_command_surface_guardrail.py <repo> [out.json]
"""
from __future__ import annotations
from pathlib import Path
import ast, json, re, sys


def read(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace') if path.exists() else ''


def enum_members(text: str, class_name: str) -> list[str]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for t in stmt.targets:
                        if isinstance(t, ast.Name):
                            out.append(t.id)
    return out


def main() -> int:
    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    gui = repo / 'src' / 'gui'
    commands_text = read(gui / 'commands.py')
    tab_text = read(gui / 'tab_actions.py')
    main_text = read(gui / 'main.py')
    helpers_text = read(gui / 'helpers.py')
    popups_text = read(gui / 'popups.py')

    members = enum_members(commands_text, 'GUICommandType')
    bot_members = [m for m in members if 'Bot' in m or 'bot' in m]
    send_queue_calls = re.findall(r'GUICommand\(GUICommandType\.([A-Za-z0-9_]+)', tab_text)
    tl_keys = sorted(set(re.findall(r"ctx\.tl\(['\"]([^'\"]+)['\"]\)", tab_text + main_text + helpers_text + popups_text)))

    proposed_command = 'ValidateBotText'
    report = {
        'repo': str(repo),
        'phase': 27,
        'gui_command_type_members': members,
        'bot_related_members': bot_members,
        'tab_actions_send_queue_command_types': sorted(set(send_queue_calls)),
        'existing_gui_tl_keys_seen_in_gui_sources': tl_keys,
        'has_execute_bot_path': 'ExecuteBot' in members and 'ExecuteBot' in send_queue_calls,
        'recommended_integration': {
            'avoid_new_async_command_for_static_validation': True,
            'reason': 'Bot text validation should run before ExecuteBot is queued, so bad scripts do not enter the backend execution path.',
            'optional_future_command': proposed_command,
            'when_to_add_future_command': 'Only add if validation becomes expensive or requires backend-only repo/game data.',
            'must_not_change': ['ExecuteBot payload shape', 'KillBot behavior', 'recent imports behavior']
        },
        'guardrails': [
            'If adding a new GUICommandType, update all command dispatch sites and tests/reports.',
            'Prefer a pure helper in tab_actions.py or a small src/gui validation module for static local checks.',
            'Never run imported bot text while validating it.',
            'Keep warnings separate from blocking errors.'
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
