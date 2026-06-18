#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]

def run(cmd):
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    return {"cmd": cmd, "returncode": p.returncode, "stdout": p.stdout[-4000:], "stderr": p.stderr[-4000:], "passed": p.returncode == 0}

def main() -> int:
    checks = [
        run([sys.executable, ".codex/scripts/deimos_diagnostics_report_import_gui_wiring_contract.py"]),
        run([sys.executable, ".codex/scripts/deimos_diagnostics_report_import_gui_contract.py"]),
        run([sys.executable, ".codex/scripts/deimos_diagnostics_report_import_gui_smoke.py"]),
        run([sys.executable, "-m", "py_compile", "src/update_system.py", "src/gui/update_check.py", "src/gui/tab_hotkeys.py", ".codex/scripts/deimos_diagnostics_report_import_gui_wiring_contract.py"]),
    ]
    blockers = [c["cmd"] for c in checks if not c["passed"]]
    report = {"phase": 69, "name": "diagnostics-report-import-gui-wiring-readiness", "passed": not blockers, "checks": checks, "blockers": blockers, "install_execution_enabled": False, "helper_launch_from_gui_enabled": False, "real_install_attempted": False}
    out = ROOT / ".codex/reports/phase69-diagnostics-report-import-gui-wiring-readiness.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if blockers else 0
if __name__ == "__main__":
    raise SystemExit(main())
