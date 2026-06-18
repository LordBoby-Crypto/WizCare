from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / ".codex" / "reports" / "phase57-staged-update-ux-readiness.json"
checks = [
    [sys.executable, str(ROOT / ".codex" / "scripts" / "deimos_staged_update_ux_summary_contract.py"), str(ROOT)],
    [sys.executable, str(ROOT / ".codex" / "scripts" / "deimos_staged_update_ux_summary_smoke.py"), str(ROOT)],
]
results = []
blockers = []
for cmd in checks:
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    entry = {"command": cmd, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
    results.append(entry)
    if proc.returncode != 0:
        blockers.append(f"check failed: {' '.join(cmd)}")
OUT.parent.mkdir(parents=True, exist_ok=True)
report = {"phase": 57, "passed": not blockers, "blockers": blockers, "checks": results}
OUT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
print(json.dumps(report, indent=2, sort_keys=True))
sys.exit(0 if not blockers else 1)
