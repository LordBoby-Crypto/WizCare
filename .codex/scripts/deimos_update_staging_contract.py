#!/usr/bin/env python3
from __future__ import annotations
import ast, json, sys
from pathlib import Path

REQUIRED_UPDATE_SYSTEM = ['stage_release_assets', 'download_asset', 'parse_sha256_checksum', 'sha256_file']
REQUIRED_GUI_SYMBOLS = ['show_staged_download_dialog', '_StageDownloadWorker', 'update_download_to_staging']
FORBIDDEN_SNIPPETS = ['os.replace(', 'shutil.move(', 'subprocess.Popen(']
REQUIRED_LOCALE_KEYS = [
    'update_download_to_staging', 'update_choose_staging_folder', 'update_staging_downloading',
    'update_staging_success_title', 'update_staging_success_message', 'update_staging_failed_title',
    'update_staging_failed_message', 'update_staging_locked', 'update_staging_cancelled',
]

def parse_defs(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'))
    except Exception:
        return set()
    return {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}

def lang_keys(path: Path) -> set[str]:
    keys = set()
    if not path.exists(): return keys
    for line in path.read_text(encoding='utf-8').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            keys.add(line.split('=', 1)[0].strip())
    return keys

def main():
    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    update_system = repo/'src/update_system.py'
    update_check = repo/'src/gui/update_check.py'
    blockers = []
    warnings = []
    us_defs = parse_defs(update_system)
    gui_defs = parse_defs(update_check)
    for name in REQUIRED_UPDATE_SYSTEM:
        if name not in us_defs: blockers.append(f'missing update_system symbol: {name}')
    gui_text = update_check.read_text(encoding='utf-8') if update_check.exists() else ''
    for name in REQUIRED_GUI_SYMBOLS:
        if name not in gui_defs and name not in gui_text: blockers.append(f'missing update GUI staging symbol/key: {name}')
    for snippet in FORBIDDEN_SNIPPETS:
        if snippet in gui_text:
            blockers.append(f'GUI staging flow must not contain forbidden installing behavior: {snippet}')
    for lang in ('en.lang', 'zh.lang'):
        keys = lang_keys(repo/'locale'/lang)
        missing = [k for k in REQUIRED_LOCALE_KEYS if k not in keys]
        if missing: blockers.append(f'{lang} missing keys: {missing}')
    result = {'ok': not blockers, 'blockers': blockers, 'warnings': warnings, 'required_locale_keys': REQUIRED_LOCALE_KEYS}
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 1 if blockers else 0
if __name__ == '__main__': raise SystemExit(main())
