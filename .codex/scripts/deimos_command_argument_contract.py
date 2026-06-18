#!/usr/bin/env python3
"""Build a static argument contract for Deimos raw commands and DeimosLang commands.

This script does not execute repo code. It scans command_parser.py and deimoslang parser/tokenizer
surfaces and emits a conservative machine-readable contract that other validators can use.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

RAW_RULES: dict[str, dict[str, Any]] = {
    "sleep": {"aliases": ["sleep", "wait", "delay"], "min_args": 1, "arg_rule": "seconds:number>=0"},
    "log": {"aliases": ["log", "debug", "print"], "min_args": 1, "arg_rule": "text-or-window-path"},
    "teleport": {"aliases": ["teleport", "tp", "setpos"], "min_args": 1, "arg_rule": "closestmob|quest|client|xyz(...)"},
    "walkto": {"aliases": ["walkto", "goto"], "min_args": 1, "arg_rule": "xyz(...)"},
    "sendkey": {"aliases": ["sendkey", "press", "presskey"], "min_args": 1, "arg_rule": "keycode [duration:number>=0]"},
    "waitfordialog": {"aliases": ["waitfordialog", "waitfordialogue"], "min_args": 0, "arg_rule": "[completion]"},
    "waitforbattle": {"aliases": ["waitforbattle", "waitforcombat"], "min_args": 0, "arg_rule": "[completion]"},
    "waitforzonechange": {"aliases": ["waitforzonechange", "wait_for_zone_change"], "min_args": 0, "arg_rule": "[from zone]|[to zone]|[completion]"},
    "waitforfree": {"aliases": ["waitforfree"], "min_args": 0, "arg_rule": "[completion]"},
    "usepotion": {"aliases": ["usepotion"], "min_args": 0, "arg_rule": "[health:number, mana:number]"},
    "buypotions": {"aliases": ["buypotions", "refillpotions", "buypots", "refillpots"], "min_args": 0, "arg_rule": "[ifneeded]"},
    "relog": {"aliases": ["logoutandin", "relog"], "min_args": 0, "arg_rule": "none"},
    "click": {"aliases": ["click"], "min_args": 0, "arg_rule": "[x:number y:number]"},
    "clickwindow": {"aliases": ["clickwindow"], "min_args": 1, "arg_rule": "window-path-list"},
    "waitforwindow": {"aliases": ["waitforwindow", "waitforpath"], "min_args": 1, "arg_rule": "window-path-list [completion]"},
    "friendtp": {"aliases": ["friendtp", "friendteleport"], "min_args": 1, "arg_rule": "icon|friend-name"},
    "entitytp": {"aliases": ["entitytp", "entityteleport"], "min_args": 1, "arg_rule": "[nav] entity-name"},
    "tozone": {"aliases": ["tozone", "to_zone"], "min_args": 1, "arg_rule": "zone-path|identifier"},
    "glideto": {"aliases": ["glideto"], "min_args": 1, "arg_rule": "xyz(...)"},
    "rotatingglideto": {"aliases": ["rotatingglideto"], "min_args": 1, "arg_rule": "xyz(...)"},
    "orbit": {"aliases": ["orbit"], "min_args": 0, "arg_rule": "camera-orbit-args"},
    "lookat": {"aliases": ["lookat"], "min_args": 1, "arg_rule": "xyz(...)"},
    "setorient": {"aliases": ["setorient"], "min_args": 1, "arg_rule": "orient(...)"},
}

DEIMOSLANG_RULES: dict[str, dict[str, Any]] = {
    "togglecombat": {"aliases": ["togglecombat", "togglecombatmode"], "arg_rule": "[on|off]"},
    "loadplaystyle": {"aliases": ["loadplaystyle"], "arg_rule": "string|identifier|expression"},
    "setdeck": {"aliases": ["setdeck"], "arg_rule": "deck-name|identifier|expression"},
    "getdeck": {"aliases": ["getdeck"], "arg_rule": "none"},
    "selectfriend": {"aliases": ["selectfriend", "choosefriend"], "arg_rule": "friend-name"},
    "plustp": {"aliases": ["plustp", "plusteleport"], "arg_rule": "xyz(...)|expression"},
    "minustp": {"aliases": ["minustp", "minusteleport"], "arg_rule": "xyz(...)|expression"},
    "autopet": {"aliases": ["autopet", "toggleautopet"], "arg_rule": "none"},
    "loggoal": {"aliases": ["loggoal"], "arg_rule": "none"},
    "logquest": {"aliases": ["logquest"], "arg_rule": "none"},
    "logzone": {"aliases": ["logzone"], "arg_rule": "none"},
    "cursor": {"aliases": ["cursor", "movecursor", "mousexy", "movemouse"], "arg_rule": "[x:number, y:number]"},
    "cursorwindow": {"aliases": ["cursorwindow", "mousewindow"], "arg_rule": "window-path"},
}


def parse_case_aliases(text: str) -> list[list[str]]:
    groups: list[list[str]] = []
    for match in re.finditer(r"case\s+([^:\n]+):", text):
        raw = match.group(1)
        aliases = re.findall(r"'([^']+)'|\"([^\"]+)\"", raw)
        group = [a or b for a, b in aliases]
        if group:
            groups.append(group)
    return groups


def extract_tokenizer_aliases(tokenizer_text: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    pattern = re.compile(r'case\s+([^:\n]+):\s*\n\s*put_simple\(TokenKind\.([a-zA-Z0-9_]+),', re.MULTILINE)
    for match in pattern.finditer(tokenizer_text):
        aliases = [a or b for a, b in re.findall(r'"([^"]+)"|\'([^\']+)\'', match.group(1))]
        if aliases:
            result.setdefault(match.group(2), []).extend(aliases)
    return result


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: deimos_command_argument_contract.py <repo> [out.json]", file=sys.stderr)
        return 2
    repo = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    command_parser = repo / "src" / "command_parser.py"
    tokenizer = repo / "src" / "deimoslang" / "tokenizer.py"
    parser = repo / "src" / "deimoslang" / "parser.py"
    cp_text = command_parser.read_text(encoding="utf-8", errors="ignore") if command_parser.exists() else ""
    tok_text = tokenizer.read_text(encoding="utf-8", errors="ignore") if tokenizer.exists() else ""
    par_text = parser.read_text(encoding="utf-8", errors="ignore") if parser.exists() else ""
    report = {
        "repo": str(repo),
        "raw_command_case_groups_detected": parse_case_aliases(cp_text),
        "deimoslang_token_aliases_detected": extract_tokenizer_aliases(tok_text),
        "raw_rules": RAW_RULES,
        "deimoslang_extra_rules": DEIMOSLANG_RULES,
        "parser_simple_command_cases": sorted(set(re.findall(r"case TokenKind\.([a-zA-Z0-9_]+):", par_text))),
        "contract_policy": {
            "strict_static_validation": "validate syntax/shape only; do not execute repo code or bot scripts",
            "unknown_command": "warn unless file is not a bot/deimoslang candidate",
            "zone_links": "validate tozone/waitforzonechange strings against traversalData when possible",
            "combat_markers": "###pX markers must use positive integer X and should not duplicate in one config block",
        },
    }
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
