#!/usr/bin/env python3
"""Aggregate Deimos release artifact readiness reports."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

def run(cmd):
    p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {'cmd': cmd, 'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}

def load(path: Path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e:
        return {'load_error': str(e)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('repo', nargs='?', default='.'); ap.add_argument('out', nargs='?')
    args=ap.parse_args(); repo=Path(args.repo)
    reports=repo/'.codex'/'reports'; reports.mkdir(parents=True,exist_ok=True)
    scripts=repo/'.codex'/'scripts'
    checksum=reports/'phase34-checksum-report.json'
    workflows=reports/'phase34-workflow-artifact-audit.json'
    r1=run([sys.executable, str(scripts/'deimos_checksum_release_artifacts.py'), str(repo), str(checksum)])
    r2=run([sys.executable, str(scripts/'deimos_release_workflow_artifact_audit.py'), str(repo), str(workflows)])
    cs=load(checksum); wf=load(workflows)
    blockers=[]; warnings=[]
    for report in (cs,wf):
        blockers.extend(report.get('blockers',[])); warnings.extend(report.get('warnings',[]))
    result={'phase':34,'checksum_report':cs,'workflow_artifact_audit':wf,'subcommands':[r1,r2],'blockers':blockers,'warnings':warnings,'release_artifact_workflow_ready':not blockers}
    if args.out:
        out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
    else:
        print(json.dumps(result,indent=2,sort_keys=True))
    return 1 if blockers else 0
if __name__=='__main__': raise SystemExit(main())
