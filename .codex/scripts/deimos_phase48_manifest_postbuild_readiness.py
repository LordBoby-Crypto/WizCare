#!/usr/bin/env python3
"""Aggregate Phase 48 release manifest post-build readiness checks."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path


def run(cmd: list[str]) -> dict:
    proc = subprocess.run(cmd, text=True, capture_output=True)
    return {'cmd':cmd, 'returncode':proc.returncode, 'stdout':proc.stdout.strip(), 'stderr':proc.stderr.strip(), 'passed':proc.returncode == 0}


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('repo', nargs='?', default='.')
    p.add_argument('output', nargs='?', default='.codex/reports/phase48-manifest-postbuild-readiness.json')
    p.add_argument('--strict-postbuild', action='store_true')
    a=p.parse_args(argv)
    repo=Path(a.repo).resolve()
    out=Path(a.output)
    py=sys.executable
    checks=[]
    checks.append(run([py, str(repo/'.codex/scripts/deimos_release_manifest_helper_integration.py'), str(repo), str(repo/'.codex/reports/phase48-helper-manifest-integration.json')]))
    cmd=[py, str(repo/'.codex/scripts/deimos_release_manifest_postbuild_validation.py'), str(repo), str(repo/'.codex/reports/phase48-release-manifest-postbuild-validation.json')]
    if a.strict_postbuild:
        cmd += ['--require-manifest','--require-artifacts','--require-helper']
    checks.append(run(cmd))
    blockers=[]; warnings=[]
    for c in checks:
        if not c['passed']:
            blockers.append('check failed: ' + ' '.join(c['cmd']))
        # Try read JSON from stdout for warnings
        try:
            if c['stdout']:
                data=json.loads(c['stdout'].splitlines()[-1])
                warnings.extend(data.get('warnings') or [])
                blockers.extend(data.get('blockers') or [])
        except Exception:
            pass
    report={'phase':48,'repo':str(repo),'strict_postbuild':a.strict_postbuild,'checks':checks,'blockers':blockers,'warnings':warnings,'passed':not blockers}
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
    print(json.dumps(report, sort_keys=True))
    return 0 if report['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
