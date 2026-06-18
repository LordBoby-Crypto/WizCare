#!/usr/bin/env python3
"""Validate that Phase 51 remains design-only and does not unlock install execution."""
from __future__ import annotations
import ast, json, re, sys
from pathlib import Path

FORBIDDEN_UNLOCK_PATTERNS = [
    r"INSTALL_EXECUTION_ENABLED\s*=\s*True",
    r"HELPER_LAUNCH_ENABLED\s*=\s*True",
    r"AUTOMATIC_INSTALL_ENABLED\s*=\s*True",
    r"subprocess\.Popen\s*\(",
    r"subprocess\.run\s*\(",
]
REQUIRED_TEXT = [
    "do not replace Deimos.exe from the GUI process",
    "checksum mismatch",
    "rollback folder",
    "final user confirmation",
    "post-install verification",
]

def main() -> int:
    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else repo / '.codex' / 'reports' / 'phase51-install-implementation-contract.json'
    path = repo / 'src' / 'update_install_plan.py'
    text = path.read_text(encoding='utf-8') if path.exists() else ''
    blockers=[]; warnings=[]
    if not path.exists(): blockers.append('src/update_install_plan.py is missing')
    else:
        try: ast.parse(text)
        except SyntaxError as e: blockers.append(f'syntax error: {e}')
        for pat in FORBIDDEN_UNLOCK_PATTERNS:
            if re.search(pat, text): blockers.append(f'forbidden unlock/execution pattern: {pat}')
        for item in REQUIRED_TEXT:
            if item not in text: warnings.append(f'missing design text: {item}')
    data={"ok": not blockers, "blockers": blockers, "warnings": warnings, "install_execution_locked": True, "helper_launch_locked": True}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(data, indent=2))
    return 0 if not blockers else 1

if __name__ == '__main__':
    raise SystemExit(main())
