#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
checks = [
    [sys.executable, str(ROOT/'.codex/scripts/deimos_diagnostics_comparison_export_gui_contract.py')],
    [sys.executable, str(ROOT/'.codex/scripts/deimos_diagnostics_comparison_export_gui_smoke.py')],
]
compile_targets = [
    ROOT/'src/update_system.py',
    ROOT/'src/gui/update_check.py',
    ROOT/'.codex/scripts/deimos_diagnostics_comparison_export_gui_contract.py',
    ROOT/'.codex/scripts/deimos_diagnostics_comparison_export_gui_smoke.py',
]
blockers=[]; results=[]
for target in compile_targets:
    proc = subprocess.run([sys.executable,'-m','py_compile',str(target)], cwd=ROOT, text=True, capture_output=True)
    results.append({'type':'compile','target':str(target.relative_to(ROOT)),'returncode':proc.returncode})
    if proc.returncode: blockers.append(f'compile failed: {target.relative_to(ROOT)}: {proc.stderr.strip()}')
for cmd in checks:
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    results.append({'type':'script','cmd':' '.join(cmd),'returncode':proc.returncode,'stdout_tail':proc.stdout[-1000:], 'stderr_tail':proc.stderr[-1000:]})
    if proc.returncode: blockers.append(f'check failed: {Path(cmd[-1]).name}')
# locale duplicate key check
for loc in ['locale/en.lang','locale/zh.lang']:
    seen=set(); dup=[]
    for line in (ROOT/loc).read_text().splitlines():
        if not line or line.lstrip().startswith('#') or '=' not in line: continue
        k=line.split('=',1)[0]
        if k in seen: dup.append(k)
        seen.add(k)
    if dup: blockers.append(f'duplicate locale keys in {loc}: {dup}')
report={'phase':66,'name':'diagnostics-comparison-export-gui-polish','passed':not blockers,'blockers':blockers,'results':results,'install_execution_enabled':False,'helper_launch_from_gui_enabled':False,'non_dry_run_enabled':False,'real_install_attempted':False}
out=ROOT/'.codex/reports/phase66-diagnostics-comparison-export-gui-readiness.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2, sort_keys=True))
print(json.dumps(report, indent=2, sort_keys=True))
raise SystemExit(0 if not blockers else 1)
