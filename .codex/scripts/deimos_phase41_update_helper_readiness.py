#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

def run(repo: Path, script: str, report: Path):
    proc = subprocess.run([sys.executable, str(repo/'.codex/scripts'/script), str(repo), str(report)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    data = json.loads(report.read_text(encoding='utf-8')) if report.exists() else {'passed': False, 'blockers': [proc.stderr or 'report missing']}
    return proc.returncode, data

def main() -> int:
    repo = Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')
    out = Path(sys.argv[2]) if len(sys.argv)>2 else repo/'.codex/reports/phase41-update-helper-readiness.json'
    report_dir = out.parent; report_dir.mkdir(parents=True, exist_ok=True)
    checks=[]; blockers=[]; warnings=[]
    for script, name in [
        ('deimos_update_helper_contract.py','contract'),
        ('deimos_update_helper_smoke.py','smoke'),
    ]:
        code, data = run(repo, script, report_dir/f'phase41-{name}.json')
        checks.append({'name': name, 'returncode': code, 'passed': bool(data.get('passed')), 'report': data})
        blockers.extend(data.get('blockers') or [])
        warnings.extend(data.get('warnings') or [])
    report={'phase':41,'script':'deimos_phase41_update_helper_readiness','passed':not blockers,'blockers':blockers,'warnings':warnings,'checks':checks}
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if not blockers else 1
if __name__=='__main__': raise SystemExit(main())
