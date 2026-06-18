#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

def run(root: Path, script: str) -> dict:
    p=subprocess.run([sys.executable, str(root/'.codex/scripts'/script), str(root)], text=True, capture_output=True)
    try: data=json.loads(p.stdout)
    except Exception: data={'passed':False,'blockers':[f'{script} produced non-json output'],'stdout':p.stdout,'stderr':p.stderr}
    data['returncode']=p.returncode
    return data

def main() -> int:
    root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')
    checks=[run(root,'deimos_update_helper_scaffold_contract.py'), run(root,'deimos_update_helper_scaffold_smoke.py')]
    blockers=[]; warnings=[]
    for c in checks:
        blockers.extend(c.get('blockers',[]) or [])
        warnings.extend(c.get('warnings',[]) or [])
        if c.get('returncode') not in (0, None): blockers.append(f"{c.get('check','unknown')} returned {c.get('returncode')}")
    result={'phase':42,'check':'update_helper_implementation_scaffold_readiness','passed':not blockers,'blockers':blockers,'warnings':warnings,'checks':checks}
    out=root/'.codex/reports/phase42-update-helper-scaffold-readiness.json'; out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 0 if not blockers else 1
if __name__ == '__main__': raise SystemExit(main())
