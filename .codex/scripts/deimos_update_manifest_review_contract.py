#!/usr/bin/env python3
from __future__ import annotations
import ast,json,sys
from pathlib import Path

REQUIRED_UPDATE_SYMBOLS=['build_staged_asset_review']
REQUIRED_GUI_SYMBOLS=['show_staged_update_review_dialog','_format_review_text','update_review_staged_files']
REQUIRED_LOCALE_KEYS=['update_review_staged_files','update_review_title','update_review_summary','update_review_release_tag','update_review_checksum_status','update_review_install_locked','update_review_files_header','update_review_manifest_missing']
FORBIDDEN=['os.replace(','shutil.move(','subprocess.Popen(','QProcess.startDetached(']

def defs(path:Path)->set[str]:
    try: tree=ast.parse(path.read_text(encoding='utf-8'))
    except Exception: return set()
    return {n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}

def keys(path:Path)->set[str]:
    out=set()
    if not path.exists(): return out
    for line in path.read_text(encoding='utf-8').splitlines():
        if '=' in line and not line.lstrip().startswith('#'): out.add(line.split('=',1)[0].strip())
    return out

def main():
    repo=Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')
    out=Path(sys.argv[2]) if len(sys.argv)>2 else None
    blockers=[]; warnings=[]
    us=repo/'src/update_system.py'; gui=repo/'src/gui/update_check.py'
    us_defs=defs(us); gui_defs=defs(gui); gui_text=gui.read_text(encoding='utf-8') if gui.exists() else ''
    for s in REQUIRED_UPDATE_SYMBOLS:
        if s not in us_defs: blockers.append(f'missing update_system symbol: {s}')
    for s in REQUIRED_GUI_SYMBOLS:
        if s not in gui_defs and s not in gui_text: blockers.append(f'missing update review GUI symbol/key: {s}')
    for s in FORBIDDEN:
        if s in gui_text: blockers.append(f'update review GUI must not contain installer behavior: {s}')
    for lang in ('en.lang','zh.lang'):
        missing=[k for k in REQUIRED_LOCALE_KEYS if k not in keys(repo/'locale'/lang)]
        if missing: blockers.append(f'{lang} missing phase39 keys: {missing}')
    result={'ok':not blockers,'phase':39,'blockers':blockers,'warnings':warnings,'required_locale_keys':REQUIRED_LOCALE_KEYS}
    if out:
        out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2)); return 1 if blockers else 0
if __name__=='__main__': raise SystemExit(main())
