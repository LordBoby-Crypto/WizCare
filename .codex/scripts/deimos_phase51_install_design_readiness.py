#!/usr/bin/env python3
"""Aggregate Phase 51 install implementation design readiness."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

def run(cmd):
    p=subprocess.run(cmd, text=True, capture_output=True)
    return {"cmd": cmd, "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}

def main() -> int:
    repo=Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')
    out=Path(sys.argv[2]) if len(sys.argv)>2 else repo/'.codex'/'reports'/'phase51-install-design-readiness.json'
    py=sys.executable
    results=[]
    results.append(run([py, str(repo/'.codex/scripts/deimos_update_install_implementation_contract.py'), str(repo), str(repo/'.codex/reports/phase51-install-contract.json')]))
    results.append(run([py, str(repo/'.codex/scripts/deimos_update_install_implementation_design.py'), str(repo), str(repo/'.codex/reports/phase51-install-design.json')]))
    blockers=[]
    for r in results:
        if r['returncode']!=0: blockers.append({'cmd': r['cmd'], 'stderr': r['stderr'], 'stdout': r['stdout']})
    data={"ok": not blockers, "blockers": blockers, "results": results, "install_execution_enabled": False, "helper_launch_enabled": False, "automatic_install_enabled": False}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps({"ok": data['ok'], "blockers": len(blockers), "install_execution_enabled": False}, indent=2))
    return 0 if not blockers else 1

if __name__=='__main__':
    raise SystemExit(main())
