#!/usr/bin/env python3
"""Aggregate Phase 53 helper/install-harness readiness."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path


def run(cmd):
    p=subprocess.run(cmd,text=True,capture_output=True)
    data=None
    try: data=json.loads(p.stdout)
    except Exception: data={"stdout":p.stdout,"stderr":p.stderr}
    return {"cmd":cmd,"returncode":p.returncode,"data":data,"stderr":p.stderr[-1000:]}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root', nargs='?', default='.'); ap.add_argument('out', nargs='?')
    args=ap.parse_args(); root=Path(args.root).resolve()
    reports=root/'.codex/reports'; reports.mkdir(parents=True, exist_ok=True)
    checks=[]
    checks.append(run([sys.executable, str(root/'.codex/scripts/deimos_helper_install_dryrun_contract.py'), str(root), str(reports/'phase53-contract.json')]))
    checks.append(run([sys.executable, str(root/'.codex/scripts/deimos_helper_install_dryrun_integration.py'), str(reports/'phase53-integration.json')]))
    blockers=[]
    for c in checks:
        if c['returncode']!=0: blockers.append('check failed: '+' '.join(map(str,c['cmd'])))
        d=c.get('data') or {}
        if isinstance(d,dict): blockers.extend(d.get('blockers',[]))
    payload={"phase":53,"name":"helper install dry-run harness readiness","passed":not blockers,"blockers":blockers,"checks":checks,"install_execution_enabled":False,"helper_launch_from_gui_enabled":False,"non_dry_run_enabled":False}
    if args.out: Path(args.out).write_text(json.dumps(payload,indent=2,sort_keys=True), encoding='utf-8')
    print(json.dumps(payload,indent=2,sort_keys=True)); return 0 if payload['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
