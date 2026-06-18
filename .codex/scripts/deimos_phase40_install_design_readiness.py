#!/usr/bin/env python3
"""Aggregate Phase 40 install-design readiness checks."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

def run(cmd):
    p=subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {"cmd": cmd, "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}

def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv)>1 else Path.cwd()
    out = Path(sys.argv[2]) if len(sys.argv)>2 else root/'.codex/reports/phase40-install-design-readiness.json'
    py=sys.executable
    checks=[
        run([py, str(root/'.codex/scripts/deimos_update_install_design_contract.py'), str(root), str(root/'.codex/reports/phase40-install-design-contract.json')]),
        run([py, str(root/'.codex/scripts/deimos_update_install_design_smoke.py'), str(root), str(root/'.codex/reports/phase40-install-design-smoke.json')]),
    ]
    blockers=[]
    for c in checks:
        if c['returncode']!=0:
            blockers.append('failed: '+' '.join(c['cmd']))
    report={"passed": not blockers, "blockers": blockers, "checks": checks}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({"passed": report['passed'], "blockers": blockers}, indent=2))
    return 0 if not blockers else 1
if __name__ == '__main__':
    raise SystemExit(main())
