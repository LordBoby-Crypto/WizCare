#!/usr/bin/env python3
"""Phase 53 contract checker for helper/install-harness integration."""
from __future__ import annotations
import argparse, json
from pathlib import Path

REQUIRED = [
    ".codex/scripts/deimos_helper_install_dryrun_integration.py",
    ".codex/scripts/deimos_update_install_test_harness.py",
    "libs/updater_helper/deimos_updater_helper.py",
]
FORBIDDEN_SNIPPETS = [
    "helper_launch_from_gui_enabled = True",
    "install_execution_enabled = True",
    "non_dry_run_enabled = True",
]


def check(root: Path) -> dict:
    blockers=[]; warnings=[]
    for rel in REQUIRED:
        if not (root/rel).exists(): blockers.append(f"missing required file: {rel}")
    integ = root/".codex/scripts/deimos_helper_install_dryrun_integration.py"
    if integ.exists():
        text = integ.read_text(encoding='utf-8')
        for token in ["--dry-run", "real_install_attempted", "install_execution_enabled", "helper_launch_from_gui_enabled", "run_harness_scenarios"]:
            if token not in text: blockers.append(f"integration script missing token: {token}")
        for forbidden in FORBIDDEN_SNIPPETS:
            if forbidden in text: blockers.append(f"unsafe enablement detected: {forbidden}")
    helper = root/"libs/updater_helper/deimos_updater_helper.py"
    if helper.exists():
        ht = helper.read_text(encoding='utf-8')
        if "Phase 42 helper scaffold only allows --dry-run" not in ht:
            warnings.append("helper dry-run lock message not found; verify non-dry-run is still blocked")
    return {"phase":53,"passed": not blockers,"blockers":blockers,"warnings":warnings}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root', nargs='?', default='.'); ap.add_argument('out', nargs='?')
    args=ap.parse_args(); payload=check(Path(args.root).resolve())
    if args.out: Path(args.out).write_text(json.dumps(payload,indent=2,sort_keys=True), encoding='utf-8')
    print(json.dumps(payload,indent=2,sort_keys=True)); return 0 if payload['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
