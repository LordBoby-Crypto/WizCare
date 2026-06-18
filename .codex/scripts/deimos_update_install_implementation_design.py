#!/usr/bin/env python3
"""Emit the Phase 51 update install implementation design as JSON."""
from __future__ import annotations
import json, sys
from pathlib import Path


def main() -> int:
    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else repo / '.codex' / 'reports' / 'phase51-install-implementation-design.json'
    sys.path.insert(0, str(repo))
    from src.update_install_plan import build_locked_install_summary
    data = build_locked_install_summary()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps({"ok": True, "out": str(out), "install_execution_enabled": data["install_execution_enabled"], "locked": data["locked"]}, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
