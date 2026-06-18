#!/usr/bin/env python3
"""Phase 56 smoke test for helper dry-run log detection states."""
from __future__ import annotations
import hashlib
import json
import sys
import tempfile
from pathlib import Path


def _write_release_files(stage: Path) -> tuple[Path, Path, Path]:
    exe = stage / "Deimos.exe"
    exe.write_bytes(b"fake-deimos-phase56")
    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    sha = stage / "Deimos.exe.sha256"
    sha.write_text(f"{digest}  Deimos.exe\n", encoding="utf-8")
    manifest = stage / "release-manifest.json"
    manifest.write_text(json.dumps({"tag": "v56.0.0", "phase": 56}), encoding="utf-8")
    return exe, sha, manifest


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else root / ".codex" / "reports" / "phase56-helper-log-detection-smoke.json"
    sys.path.insert(0, str(root))
    from src.update_system import (  # type: ignore
        HELPER_LOG_NAME,
        STABLE_CHECKSUM_ASSET,
        STABLE_EXE_ASSET,
        STABLE_MANIFEST_ASSET,
        ReleaseAsset,
        ReleaseInfo,
        build_helper_dry_run_review,
    )

    blockers: list[str] = []
    cases: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="deimos-phase56-") as tmp:
        stage = Path(tmp)
        exe, sha, manifest = _write_release_files(stage)
        release = ReleaseInfo(
            tag_name="v56.0.0",
            name="Phase 56 Test",
            html_url="https://example.invalid/release",
            prerelease=False,
            draft=False,
            raw={},
            assets={
                STABLE_EXE_ASSET: ReleaseAsset(STABLE_EXE_ASSET, "https://example.invalid/Deimos.exe", exe.stat().st_size),
                STABLE_CHECKSUM_ASSET: ReleaseAsset(STABLE_CHECKSUM_ASSET, "https://example.invalid/Deimos.exe.sha256", sha.stat().st_size),
                STABLE_MANIFEST_ASSET: ReleaseAsset(STABLE_MANIFEST_ASSET, "https://example.invalid/release-manifest.json", manifest.stat().st_size),
            },
        )
        paths = {STABLE_EXE_ASSET: exe, STABLE_CHECKSUM_ASSET: sha, STABLE_MANIFEST_ASSET: manifest}
        missing_review = build_helper_dry_run_review(release, paths)
        cases["missing"] = missing_review.get("helper_log_status")
        if cases["missing"] != "missing":
            blockers.append(f"missing log classified as {cases['missing']}")

        log = stage / HELPER_LOG_NAME
        log.write_text(json.dumps({"event": "manifest_loaded"}) + "\n", encoding="utf-8")
        incomplete_review = build_helper_dry_run_review(release, paths)
        cases["incomplete"] = incomplete_review.get("helper_log_status")
        if cases["incomplete"] != "incomplete":
            blockers.append(f"incomplete log classified as {cases['incomplete']}")

        log.write_text("not json\n", encoding="utf-8")
        invalid_review = build_helper_dry_run_review(release, paths)
        cases["invalid"] = invalid_review.get("helper_log_status")
        if cases["invalid"] != "invalid":
            blockers.append(f"invalid log classified as {cases['invalid']}")

        log.write_text("\n".join(json.dumps({"event": e}) for e in ["manifest_loaded", "checksum_verified", "dry_run_complete"]) + "\n", encoding="utf-8")
        valid_review = build_helper_dry_run_review(release, paths)
        cases["valid"] = valid_review.get("helper_log_status")
        if cases["valid"] != "valid" or valid_review.get("helper_log_valid") is not True:
            blockers.append(f"valid log classified as {cases['valid']}")

    report = {
        "phase": 56,
        "passed": not blockers,
        "cases": cases,
        "blockers": blockers,
        "real_install_attempted": False,
        "helper_launch_from_gui_enabled": False,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not blockers else 1

if __name__ == "__main__":
    raise SystemExit(main())
