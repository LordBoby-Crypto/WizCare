#!/usr/bin/env python3
"""Verify Phase 52 updater install test harness contract."""
from __future__ import annotations
import ast, json, sys
from pathlib import Path

REQUIRED_NAMES = {
    "run_all",
    "run_scenario",
    "simulate_install",
    "create_fake_environment",
    "EXIT_SUCCESS",
    "EXIT_CHECKSUM_FAILED",
    "EXIT_ROLLBACK_USED",
}
FORBIDDEN_SNIPPETS = ["subprocess.Popen", "os.replace", "Path.replace", "startfile", "relaunch"]

def main() -> int:
    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    harness = repo / '.codex/scripts/deimos_update_install_test_harness.py'
    blockers = []
    warnings = []
    if not harness.exists():
        blockers.append(f"missing {harness}")
        source = ""
        names = set()
    else:
        source = harness.read_text(encoding='utf-8')
        tree = ast.parse(source)
        names = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
        names |= {t.id for n in tree.body if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name)}
    for name in sorted(REQUIRED_NAMES - names):
        blockers.append(f"missing required harness symbol: {name}")
    for snippet in FORBIDDEN_SNIPPETS:
        if snippet in source:
            blockers.append(f"forbidden real-install snippet found: {snippet}")
    if "real_install_attempted\": False" not in source and 'real_install_attempted": False' not in source:
        warnings.append("could not statically find real_install_attempted false marker")
    payload = {"phase": 52, "passed": not blockers, "blockers": blockers, "warnings": warnings}
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not blockers else 1
if __name__ == '__main__':
    raise SystemExit(main())
