#!/usr/bin/env python3
from pathlib import Path
import json, sys, ast

def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else root/'.codex/reports/phase54-helper-dryrun-gui-contract.json'
    blockers=[]; warnings=[]
    update_system = root/'src/update_system.py'
    update_gui = root/'src/gui/update_check.py'
    for p in [update_system, update_gui]:
        if not p.exists(): blockers.append(f'missing {p}')
        else:
            try: ast.parse(p.read_text(encoding='utf-8'))
            except SyntaxError as e: blockers.append(f'syntax error in {p}: {e}')
    us = update_system.read_text(encoding='utf-8') if update_system.exists() else ''
    ug = update_gui.read_text(encoding='utf-8') if update_gui.exists() else ''
    for token in ['build_helper_dry_run_review','helper_launch_enabled','non_dry_run_enabled','dry_run_required_events']:
        if token not in us: blockers.append(f'update_system missing {token}')
    for token in ['show_helper_dry_run_review_dialog','update_helper_dry_run_button','build_helper_dry_run_review']:
        if token not in ug: blockers.append(f'update_check missing {token}')
    for lang in ['en.lang','zh.lang']:
        lp=root/'locale'/lang
        txt=lp.read_text(encoding='utf-8') if lp.exists() else ''
        for key in ['update_helper_dry_run_button','update_helper_dry_run_title','update_helper_dry_run_summary','update_helper_dry_run_locked','update_helper_dry_run_command','update_helper_dry_run_log_events','update_helper_dry_run_log_missing']:
            if f'{key}=' not in txt: blockers.append(f'{lang} missing {key}')
    result={'passed': not blockers, 'blockers': blockers, 'warnings': warnings}
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 0 if not blockers else 1
if __name__ == '__main__': raise SystemExit(main())
