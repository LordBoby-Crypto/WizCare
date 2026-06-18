#!/usr/bin/env python3
from __future__ import annotations
import json, py_compile, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/'.codex/reports/phase62-diagnostics-comparison-review-readiness.json'

def run(script):
    p=subprocess.run([sys.executable, script], cwd=ROOT, text=True, capture_output=True)
    return {"script": script, "returncode": p.returncode, "stdout": p.stdout[-2000:], "stderr": p.stderr[-2000:]}

def main() -> int:
    blockers=[]; checks=[]
    compile_targets=['src/update_system.py','.codex/scripts/deimos_staged_update_diagnostics_comparison_review.py','.codex/scripts/deimos_staged_update_diagnostics_comparison_review_contract.py','.codex/scripts/deimos_staged_update_diagnostics_comparison_review_smoke.py']
    for target in compile_targets:
        try:
            py_compile.compile(str(ROOT/target), doraise=True)
            checks.append({"name": f"compile:{target}", "passed": True})
        except Exception as exc:
            blockers.append(f"compile failed for {target}: {exc}")
            checks.append({"name": f"compile:{target}", "passed": False, "error": str(exc)})
    for script in ['.codex/scripts/deimos_staged_update_diagnostics_comparison_review_contract.py','.codex/scripts/deimos_staged_update_diagnostics_comparison_review_smoke.py']:
        res=run(script); checks.append({"name": script, "passed": res['returncode']==0, "result": res})
        if res['returncode']!=0: blockers.append(f"{script} failed")
    required=[
        'build_diagnostics_comparison_review',
        'compare_staged_update_diagnostics_bundles_for_review',
        'STAGED_DIAGNOSTICS_COMPARISON_REVIEW_VERSION',
    ]
    text=(ROOT/'src/update_system.py').read_text(encoding='utf-8')
    for token in required:
        ok=token in text; checks.append({"name": f"token:{token}", "passed": ok})
        if not ok: blockers.append(f"missing token {token}")
    out={"phase": 62, "passed": not blockers, "blockers": blockers, "checks": checks, "review_only": True, "install_execution_enabled": False, "helper_launch_from_gui_enabled": False, "non_dry_run_enabled": False, "real_install_attempted": False}
    REPORT.parent.mkdir(parents=True, exist_ok=True); REPORT.write_text(json.dumps(out, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if not blockers else 1
if __name__=='__main__':
    raise SystemExit(main())
