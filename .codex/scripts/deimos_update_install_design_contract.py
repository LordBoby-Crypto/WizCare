#!/usr/bin/env python3
"""Check that update install design review remains disabled/review-only."""
from __future__ import annotations
import json, sys
from pathlib import Path

FORBIDDEN_PATTERNS = [
    "os.replace(",
    "os.rename(",
    "shutil.move(",
    "subprocess.Popen(",
    "subprocess.run(",
    "startfile(",
]
REQUIRED_TOKENS = [
    "build_update_install_design_review",
    "INSTALL_ENABLED = False",
    "INSTALL_REVIEW_ONLY = True",
    "INSTALL_HELPER_REQUIRED = True",
    "explicitly_forbidden_in_gui_process",
    "rollback_rules",
    "locked_file_handling_rules",
]

def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else root/'.codex/reports/phase40-install-design-contract.json'
    path = root/'src/update_system.py'
    text = path.read_text(encoding='utf-8')
    blockers=[]
    for token in REQUIRED_TOKENS:
        if token not in text:
            blockers.append(f"missing required token: {token}")
    # Only evaluate forbidden patterns inside update_system.py after the phase marker.
    phase_text = text.split('PHASE40_INSTALL_DESIGN_REVIEW',1)[-1]
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in phase_text:
            blockers.append(f"forbidden executable/install operation in install design section: {pattern}")
    report={"passed": not blockers, "blockers": blockers, "checked": str(path)}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if not blockers else 1
if __name__ == '__main__':
    raise SystemExit(main())
