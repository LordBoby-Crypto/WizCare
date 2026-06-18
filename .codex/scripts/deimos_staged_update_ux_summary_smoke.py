from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
sys.path.insert(0, str(ROOT))

from src.update_system import (
    HELPER_LOG_NAME,
    ReleaseAsset,
    ReleaseInfo,
    build_staged_update_ux_summary,
)

def make_release(exe_size: int, checksum_size: int, manifest_size: int) -> ReleaseInfo:
    return ReleaseInfo(
        tag_name="v9.9.9-test",
        name="Test Release",
        html_url="https://example.invalid/release",
        prerelease=False,
        draft=False,
        assets={
            "Deimos.exe": ReleaseAsset("Deimos.exe", "https://example.invalid/Deimos.exe", exe_size),
            "Deimos.exe.sha256": ReleaseAsset("Deimos.exe.sha256", "https://example.invalid/Deimos.exe.sha256", checksum_size),
            "release-manifest.json": ReleaseAsset("release-manifest.json", "https://example.invalid/release-manifest.json", manifest_size),
        },
        raw={},
    )

with tempfile.TemporaryDirectory(prefix="deimos-phase57-") as tmp:
    stage = Path(tmp)
    exe = stage / "Deimos.exe"
    exe.write_bytes(b"fake exe content")
    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    checksum = stage / "Deimos.exe.sha256"
    checksum.write_text(f"{digest}  Deimos.exe\n", encoding="utf-8")
    manifest = stage / "release-manifest.json"
    manifest.write_text(json.dumps({"version": "9.9.9-test", "assets": ["Deimos.exe"]}), encoding="utf-8")
    log = stage / HELPER_LOG_NAME
    log.write_text('\n'.join([
        json.dumps({"event": "manifest_loaded"}),
        json.dumps({"event": "plan_built"}),
        json.dumps({"event": "checksum_verified"}),
        json.dumps({"event": "dry_run_complete"}),
    ]) + '\n', encoding="utf-8")
    release = make_release(exe.stat().st_size, checksum.stat().st_size, manifest.stat().st_size)
    report = build_staged_update_ux_summary(release, {
        "Deimos.exe": exe,
        "Deimos.exe.sha256": checksum,
        "release-manifest.json": manifest,
    })

blockers = []
if report.get("checksum_status") != "verified":
    blockers.append("checksum status should be verified")
if report.get("helper_log_status") != "valid":
    blockers.append("helper dry-run log should be valid")
if report.get("severity") != "ready_for_review":
    blockers.append(f"expected ready_for_review severity, got {report.get('severity')}")
if report.get("install_locked") is not True:
    blockers.append("install must remain locked")
print(json.dumps({"passed": not blockers, "blockers": blockers, "report": report}, indent=2, sort_keys=True))
sys.exit(0 if not blockers else 1)
