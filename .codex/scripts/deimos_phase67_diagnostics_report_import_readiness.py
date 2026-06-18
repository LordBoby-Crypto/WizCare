#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
checks = [
    [sys.executable, str(ROOT / ".codex/scripts/deimos_diagnostics_comparison_report_import_contract.py")],
    [sys.executable, str(ROOT / ".codex/scripts/deimos_diagnostics_comparison_report_import_smoke.py")],
]
compile_targets = [
    ROOT / "src/update_system.py",
    ROOT / "src/gui/update_check.py",
    ROOT / ".codex/scripts/deimos_diagnostics_comparison_report_import.py",
    ROOT / ".codex/scripts/deimos_diagnostics_comparison_report_import_contract.py",
    ROOT / ".codex/scripts/deimos_diagnostics_comparison_report_import_smoke.py",
]
blockers: list[str] = []
results: list[dict] = []
for target in compile_targets:
    proc = subprocess.run([sys.executable, "-m", "py_compile", str(target)], cwd=ROOT, text=True, capture_output=True)
    results.append({"type": "compile", "target": str(target.relative_to(ROOT)), "returncode": proc.returncode, "stderr_tail": proc.stderr[-1000:]})
    if proc.returncode:
        blockers.append(f"compile failed: {target.relative_to(ROOT)}")
for cmd in checks:
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    results.append({"type": "script", "cmd": " ".join(cmd), "returncode": proc.returncode, "stdout_tail": proc.stdout[-1000:], "stderr_tail": proc.stderr[-1000:]})
    if proc.returncode:
        blockers.append(f"check failed: {Path(cmd[-1]).name}")
report = {
    "phase": 67,
    "name": "diagnostics-comparison-exported-report-import-review",
    "passed": not blockers,
    "blockers": blockers,
    "results": results,
    "diagnostics_report_import_read_only": True,
    "executable_payload_import": False,
    "install_execution_enabled": False,
    "helper_launch_from_gui_enabled": False,
    "non_dry_run_enabled": False,
    "real_install_attempted": False,
}
out = ROOT / ".codex/reports/phase67-diagnostics-comparison-report-import-readiness.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2, sort_keys=True))
print(json.dumps(report, indent=2, sort_keys=True))
raise SystemExit(0 if not blockers else 1)
