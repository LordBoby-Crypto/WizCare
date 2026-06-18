#!/usr/bin/env python3
"""Smoke-test non-GUI update helper behavior used by the manual update check."""
from __future__ import annotations
import json
import sys
from pathlib import Path


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    sys.path.insert(0, str(root))
    blockers = []
    checks = {}
    try:
        from src.update_system import normalize_version, is_newer_version, parse_sha256_checksum
        checks["normalize_v3_13_1"] = normalize_version("v3.13.1") == (3, 13, 1)
        checks["newer_3_14"] = is_newer_version("3.14.0", "3.13.1") is True
        checks["not_newer_same"] = is_newer_version("3.13.1", "3.13.1") is False
        checks["checksum_parse"] = parse_sha256_checksum("a" * 64 + "  Deimos.exe\n") == "a" * 64
    except Exception as exc:
        blockers.append(f"update_system_import_or_smoke_failed: {exc}")
    for key, ok in checks.items():
        if not ok:
            blockers.append(key)
    report = {"checks": checks, "blockers": blockers, "passed": not blockers}
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    else:
        print(json.dumps(report, indent=2))
    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
