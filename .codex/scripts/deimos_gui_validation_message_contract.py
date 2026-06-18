#!/usr/bin/env python3
"""Check locale readiness for GUI bot validation messages.

Usage: python deimos_gui_validation_message_contract.py <repo> [out.json]
"""
from __future__ import annotations
from pathlib import Path
import json, sys

REQUIRED_KEYS = [
    'validate_bot', 'bot_validation_title', 'bot_validation_errors',
    'bot_validation_warnings', 'bot_validation_run_anyway',
    'bot_validation_cancelled', 'bot_validation_no_issues',
    'bot_validation_unknown_command', 'bot_validation_bad_arguments',
    'bot_validation_bad_coordinate', 'bot_validation_bad_selector',
    'bot_validation_unknown_zone', 'bot_validation_missing_combat_marker'
]

SUGGESTED_EN = {
    'validate_bot': 'Validate Bot',
    'bot_validation_title': 'Bot Validation',
    'bot_validation_errors': 'Bot validation found errors.',
    'bot_validation_warnings': 'Bot validation found warnings.',
    'bot_validation_run_anyway': 'Run Anyway',
    'bot_validation_cancelled': 'Bot run cancelled.',
    'bot_validation_no_issues': 'No bot validation issues found.',
    'bot_validation_unknown_command': 'Unknown command: {command}',
    'bot_validation_bad_arguments': 'Invalid arguments for {command}.',
    'bot_validation_bad_coordinate': 'Invalid coordinate or orientation value.',
    'bot_validation_bad_selector': 'Invalid client selector.',
    'bot_validation_unknown_zone': 'Unknown or unlinked zone: {zone}',
    'bot_validation_missing_combat_marker': 'Combat marker section is missing or incomplete.'
}

SUGGESTED_ZH = {
    'validate_bot': 'Validate Bot',
    'bot_validation_title': 'Bot Validation',
    'bot_validation_errors': 'Bot validation found errors.',
    'bot_validation_warnings': 'Bot validation found warnings.',
    'bot_validation_run_anyway': 'Run Anyway',
    'bot_validation_cancelled': 'Bot run cancelled.',
    'bot_validation_no_issues': 'No bot validation issues found.',
    'bot_validation_unknown_command': 'Unknown command: {command}',
    'bot_validation_bad_arguments': 'Invalid arguments for {command}.',
    'bot_validation_bad_coordinate': 'Invalid coordinate or orientation value.',
    'bot_validation_bad_selector': 'Invalid client selector.',
    'bot_validation_unknown_zone': 'Unknown or unlinked zone: {zone}',
    'bot_validation_missing_combat_marker': 'Combat marker section is missing or incomplete.'
}


def parse_lang(path: Path) -> dict[str, str]:
    data = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        s = line.strip()
        if not s or s.startswith('#') or '=' not in s:
            continue
        k, v = s.split('=', 1)
        data[k.strip()] = v.strip()
    return data


def main() -> int:
    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    locale = repo / 'locale'
    langs = {p.stem: parse_lang(p) for p in sorted(locale.glob('*.lang'))}
    all_keys = set().union(*(set(v.keys()) for v in langs.values())) if langs else set()
    missing_by_lang = {name: sorted(set(REQUIRED_KEYS) - set(keys)) for name, keys in langs.items()}
    parity = {name: sorted(all_keys - set(keys)) for name, keys in langs.items()}
    report = {
        'repo': str(repo),
        'phase': 27,
        'required_keys': REQUIRED_KEYS,
        'languages_found': sorted(langs),
        'missing_required_keys_by_language': missing_by_lang,
        'existing_locale_parity_missing_by_language': parity,
        'ready_for_gui_validation_patch': all(not v for v in missing_by_lang.values()) and all(not v for v in parity.values()),
        'suggested_en_values': SUGGESTED_EN,
        'suggested_zh_values': SUGGESTED_ZH,
        'policy': [
            'Codex must update every .lang file for new GUI validation strings.',
            'Codex may use English fallback text in zh.lang only as a temporary explicit TODO, not as completed translation.',
            'Codex must preserve placeholder names like {command} and {zone} across languages.'
        ]
    }
    text = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + '\n', encoding='utf-8')
    else:
        print(text)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
