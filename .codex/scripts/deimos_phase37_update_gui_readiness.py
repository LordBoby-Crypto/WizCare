#!/usr/bin/env python3
"""Aggregate Phase 37 manual update-check GUI readiness."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path


def run(cmd):
    proc = subprocess.run(cmd, text=True, capture_output=True)
    return {"cmd": cmd, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else root / ".codex/reports/phase37-update-gui-readiness.json"
    reports_dir = root / ".codex/reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    scripts = root / ".codex/scripts"
    runs = [
        run([sys.executable, str(scripts / "deimos_update_gui_integration_check.py"), str(root), str(reports_dir / "phase37-update-gui-integration.json")]),
        run([sys.executable, str(scripts / "deimos_update_gui_smoke.py"), str(root), str(reports_dir / "phase37-update-gui-smoke.json")]),
        run([sys.executable, "-m", "py_compile", str(root / "src/gui/update_check.py"), str(root / "src/gui/tab_hotkeys.py"), str(root / "src/update_system.py")]),
    ]
    blockers = [r for r in runs if r["returncode"] != 0]
    report = {"phase": 37, "name": "manual update-check gui integration", "runs": runs, "blockers": blockers, "passed": not blockers}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
