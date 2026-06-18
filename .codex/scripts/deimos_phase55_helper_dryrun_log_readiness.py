#!/usr/bin/env python3
"""Aggregate Phase 55 readiness check."""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys, tempfile, shutil
from pathlib import Path

def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding='utf-8')

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('repo_root')
    ap.add_argument('out', nargs='?')
    args=ap.parse_args()
    root=Path(args.repo_root).resolve()
    py=sys.executable
    reports=root/'.codex/reports'
    reports.mkdir(parents=True, exist_ok=True)
    checks=[]
    def run(name, cmd):
        proc=subprocess.run(cmd, text=True, capture_output=True)
        payload={'name':name,'command':cmd,'returncode':proc.returncode,'stdout_tail':proc.stdout[-2000:],'stderr_tail':proc.stderr[-2000:],'passed':proc.returncode==0}
        checks.append(payload)
        return proc
    run('contract',[py, str(root/'.codex/scripts/deimos_helper_dryrun_log_contract.py'), str(root), str(reports/'phase55-contract.json')])
    temp=Path(tempfile.mkdtemp(prefix='deimos-phase55-staged-'))
    try:
        stage=temp/'stage'
        stage.mkdir(parents=True, exist_ok=True)
        exe=stage/'Deimos.exe'
        data=b'PHASE55-STAGED-DEIMOS-DRY-RUN\n'
        exe.write_bytes(data)
        digest=hashlib.sha256(data).hexdigest()
        (stage/'Deimos.exe.sha256').write_text(f'{digest}  Deimos.exe\n', encoding='utf-8')
        run('generate-dry-run-log',[py, str(root/'.codex/scripts/deimos_helper_dryrun_log_generator.py'), str(root), str(stage), str(reports/'phase55-generated-log-report.json')])
        generated=json.loads((reports/'phase55-generated-log-report.json').read_text(encoding='utf-8')) if (reports/'phase55-generated-log-report.json').exists() else {}
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    blockers=[]
    for c in checks:
        if not c['passed']: blockers.append(f"{c['name']} failed")
    if generated and not generated.get('passed'):
        blockers.append('generated dry-run log report did not pass')
    payload={'phase':55,'name':'helper dry-run log generation readiness','passed':not blockers,'checks':checks,'generated_log_report':generated,'blockers':blockers,'install_execution_enabled':False,'helper_launch_from_gui_enabled':False,'real_install_attempted':False}
    if args.out: write_json(Path(args.out), payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not blockers else 1
if __name__=='__main__': raise SystemExit(main())
