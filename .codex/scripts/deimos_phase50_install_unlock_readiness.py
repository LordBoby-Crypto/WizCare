#!/usr/bin/env python3
"""Aggregate Phase 50 install unlock gate readiness."""
from __future__ import annotations
from pathlib import Path
import argparse, json, subprocess, sys

CHECKS = [
    [sys.executable, ".codex/scripts/deimos_update_install_unlock_gate.py", ".", ".codex/reports/phase50-install-unlock-gate.json"],
    [sys.executable, ".codex/scripts/deimos_update_install_unlock_gate_smoke.py", ".", ".codex/reports/phase50-install-unlock-gate-smoke.json"],
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("output", nargs="?", default=".codex/reports/phase50-install-unlock-readiness.json")
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    blockers = []
    results = []
    for cmd in CHECKS:
        proc = subprocess.run(cmd, cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        results.append({"cmd": cmd, "returncode": proc.returncode, "stdout_tail": proc.stdout[-2000:], "stderr_tail": proc.stderr[-2000:]})
        if proc.returncode != 0:
            blockers.append("check failed: " + " ".join(cmd))
    report = {
        "phase": 50,
        "check": "install_unlock_readiness",
        "ok": not blockers,
        "install_unlocked": False,
        "install_locked": True,
        "blockers": blockers,
        "results": results,
    }
    out = repo / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 1 if blockers else 0

if __name__ == "__main__":
    raise SystemExit(main())
