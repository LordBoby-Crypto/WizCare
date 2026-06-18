from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

def run(cmd):
    p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return {"cmd": cmd, "returncode": p.returncode, "output_tail": p.stdout[-4000:]}

def main(repo_root: str, out_path: str) -> int:
    root = Path(repo_root)
    reports = root / ".codex" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    steps = [
        run([sys.executable, str(root/'.codex/scripts/deimos_update_system_contract.py'), str(root), str(reports/'update-system-contract.json')]),
        run([sys.executable, str(root/'.codex/scripts/deimos_update_system_smoke.py'), str(root), str(reports/'update-system-smoke.json')]),
    ]
    blockers = [s for s in steps if s["returncode"] != 0]
    report = {"passed": not blockers, "blockers": blockers, "steps": steps}
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else ".", sys.argv[2] if len(sys.argv) > 2 else ".codex/reports/update-system-readiness.json"))
