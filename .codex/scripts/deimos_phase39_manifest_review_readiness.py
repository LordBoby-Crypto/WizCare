#!/usr/bin/env python3
from __future__ import annotations
import json,subprocess,sys
from pathlib import Path
SCRIPTS=['deimos_update_manifest_review_contract.py','deimos_update_manifest_review_smoke.py']
def run(repo:Path,name:str,reports:Path):
    out=reports/(name.replace('.py','.json'))
    proc=subprocess.run([sys.executable,str(repo/'.codex/scripts'/name),str(repo),str(out)],text=True,capture_output=True)
    data=json.loads(out.read_text(encoding='utf-8')) if out.exists() else {'ok':False,'blockers':[proc.stderr or proc.stdout]}
    return {'script':name,'returncode':proc.returncode,'ok':bool(data.get('ok')),'report':str(out),'data':data}
def main():
    repo=Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')
    out=Path(sys.argv[2]) if len(sys.argv)>2 else repo/'.codex/reports/phase39-manifest-review-readiness.json'
    reports=repo/'.codex/reports'; reports.mkdir(parents=True,exist_ok=True)
    checks=[run(repo,s,reports) for s in SCRIPTS]
    blockers=[]
    for c in checks:
        if not c['ok']: blockers.extend(c['data'].get('blockers') or [f"{c['script']} failed"])
    result={'ok':not blockers,'phase':39,'summary':'staged update manifest review UI readiness','checks':checks,'blockers':blockers}
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2)); return 1 if blockers else 0
if __name__=='__main__': raise SystemExit(main())
