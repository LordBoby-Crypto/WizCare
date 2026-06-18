#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import ast, json, sys

REQUIRED_UPDATE_SYSTEM = [
    'build_staged_update_diagnostics_bundle',
    'export_staged_update_diagnostics_bundle',
    'STAGED_DIAGNOSTICS_VERSION',
    'STAGED_DIAGNOSTICS_FILENAME',
]
REQUIRED_GUI = [
    'export_staged_update_diagnostics_dialog',
    'export_staged_update_diagnostics_bundle',
    'update_export_diagnostics',
]
REQUIRED_LOCALE_KEYS = [
    'update_export_diagnostics',
    'update_diagnostics_saved_title',
    'update_diagnostics_saved_message',
    'update_diagnostics_failed_title',
    'update_diagnostics_failed_message',
    'update_diagnostics_bundle_locked',
]

def read(path: Path) -> str:
    return path.read_text(encoding='utf-8')

def locale_keys(path: Path) -> set[str]:
    keys=set()
    for line in read(path).splitlines():
        line=line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        keys.add(line.split('=',1)[0].strip())
    return keys

def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')
    out = Path(sys.argv[2]) if len(sys.argv)>2 else root/'.codex/reports/phase59-diagnostics-export-contract.json'
    blockers=[]
    us = read(root/'src/update_system.py')
    gui = read(root/'src/gui/update_check.py')
    try:
        ast.parse(us)
        ast.parse(gui)
    except SyntaxError as exc:
        blockers.append(f'python syntax error: {exc}')
    for token in REQUIRED_UPDATE_SYSTEM:
        if token not in us:
            blockers.append(f'update_system.py missing {token}')
    for token in REQUIRED_GUI:
        if token not in gui:
            blockers.append(f'update_check.py missing {token}')
    for lp in ('locale/en.lang','locale/zh.lang'):
        keys=locale_keys(root/lp)
        for key in REQUIRED_LOCALE_KEYS:
            if key not in keys:
                blockers.append(f'{lp} missing {key}')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({'phase':59,'passed':not blockers,'blockers':blockers},indent=2), encoding='utf-8')
    return 1 if blockers else 0
if __name__ == '__main__':
    raise SystemExit(main())
