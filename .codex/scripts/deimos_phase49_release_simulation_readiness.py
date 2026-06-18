#!/usr/bin/env python3
"""Aggregate Phase 49 updater dry-run release simulation readiness."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path


def run(cmd: list[str]) -> dict:
    proc=subprocess.run(cmd, text=True, capture_output=True)
    return {'cmd':cmd,'returncode':proc.returncode,'stdout':proc.stdout[-5000:],'stderr':proc.stderr[-5000:],'passed':proc.returncode==0}


def main(argv=None) -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('repo', nargs='?', default='.')
    ap.add_argument('output', nargs='?', default='.codex/reports/phase49-release-simulation-readiness.json')
    args=ap.parse_args(argv)
    repo=Path(args.repo).resolve(); out=Path(args.output)
    py=sys.executable
    checks=[run([py, str(repo/'.codex/scripts/deimos_fake_release_simulation.py'), str(repo), str(repo/'.codex/reports/phase49-dryrun-release-simulation.json')])]
    blockers=[]; warnings=[]
    for c in checks:
        if not c['passed']:
            blockers.append('check failed: ' + ' '.join(c['cmd']))
        try:
            data=json.loads(c['stdout'].splitlines()[-1]) if c['stdout'] else {}
            blockers.extend(data.get('blockers') or [])
            warnings.extend(data.get('warnings') or [])
        except Exception:
            pass
    report={'phase':49,'repo':str(repo),'checks':checks,'blockers':blockers,'warnings':warnings,'passed':not blockers,'install_execution_locked':True,'simulation_only':True}
    out=out if out.is_absolute() else repo/out
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
    print(json.dumps(report, sort_keys=True))
    return 0 if report['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
