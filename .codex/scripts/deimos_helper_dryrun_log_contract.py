#!/usr/bin/env python3
"""Phase 55 contract check for staged helper dry-run log generation."""
from __future__ import annotations
import argparse, json, py_compile
from pathlib import Path

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('repo_root')
    ap.add_argument('out', nargs='?')
    args=ap.parse_args()
    root=Path(args.repo_root).resolve()
    blockers=[]
    checks={}
    required=[
        '.codex/scripts/deimos_helper_dryrun_log_generator.py',
        'libs/updater_helper/deimos_updater_helper.py',
        'src/update_system.py',
        'src/gui/update_check.py',
    ]
    for rel in required:
        p=root/rel
        checks[rel]=p.exists()
        if not p.exists(): blockers.append(f'missing {rel}')
    gen=root/'.codex/scripts/deimos_helper_dryrun_log_generator.py'
    if gen.exists():
        try: py_compile.compile(str(gen), doraise=True)
        except Exception as exc: blockers.append(f'generator compile failed: {exc}')
    update=(root/'src/update_system.py').read_text(encoding='utf-8') if (root/'src/update_system.py').exists() else ''
    for token in ['HELPER_LOG_NAME','build_helper_dry_run_review','helper_launch_enabled','install_execution_enabled']:
        if token not in update: blockers.append(f'update_system missing token {token}')
    payload={'phase':55,'name':'helper dry-run log contract','passed':not blockers,'checks':checks,'blockers':blockers}
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(payload,indent=2,sort_keys=True),encoding='utf-8')
    print(json.dumps(payload,indent=2,sort_keys=True))
    return 0 if not blockers else 1
if __name__=='__main__': raise SystemExit(main())
