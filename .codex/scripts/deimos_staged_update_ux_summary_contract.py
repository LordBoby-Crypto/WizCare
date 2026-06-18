from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
sys.path.insert(0, str(ROOT))

from src.update_system import build_staged_update_ux_summary, ReleaseAsset, ReleaseInfo

required_keys = {
    "review_only",
    "severity",
    "headline",
    "summary_lines",
    "checksum_status",
    "manifest_status",
    "helper_log_status",
    "install_locked",
    "blockers",
}
release = ReleaseInfo(
    tag_name="v0.0.0-test",
    name="Test Release",
    html_url="https://example.invalid/release",
    prerelease=False,
    draft=False,
    assets={
        "Deimos.exe": ReleaseAsset("Deimos.exe", "https://example.invalid/Deimos.exe", 4),
        "Deimos.exe.sha256": ReleaseAsset("Deimos.exe.sha256", "https://example.invalid/Deimos.exe.sha256", 80),
        "release-manifest.json": ReleaseAsset("release-manifest.json", "https://example.invalid/release-manifest.json", 2),
    },
    raw={},
)
report = build_staged_update_ux_summary(release, {})
missing = sorted(required_keys - set(report))
blockers = []
if missing:
    blockers.append(f"missing required keys: {missing}")
if report.get("review_only") is not True:
    blockers.append("review_only must remain true")
if report.get("install_locked") is not True:
    blockers.append("install_locked must remain true")
if not isinstance(report.get("summary_lines"), list) or not report["summary_lines"]:
    blockers.append("summary_lines must be a non-empty list")
result = {"passed": not blockers, "blockers": blockers, "report": report}
print(json.dumps(result, indent=2, sort_keys=True))
sys.exit(0 if not blockers else 1)
