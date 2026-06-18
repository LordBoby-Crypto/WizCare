#!/usr/bin/env python3
"""Smoke-test the Phase 50 install unlock gate helper function."""
from __future__ import annotations
from pathlib import Path
import argparse, importlib.util, json, sys


def load_update_system(repo: Path):
    path = repo / "src/update_system.py"
    spec = importlib.util.spec_from_file_location("deimos_phase50_update_system", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("output", nargs="?", default=".codex/reports/phase50-install-unlock-gate-smoke.json")
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    blockers: list[str] = []

    try:
        mod = load_update_system(repo)
        review = mod.build_install_unlock_gate_review()
        if review.get("install_unlocked") is not False:
            blockers.append("install_unlocked must be false")
        if review.get("install_locked") is not True:
            blockers.append("install_locked must be true")
        if not review.get("blockers"):
            blockers.append("empty evidence should produce blockers")

        validish_release_manifest = {
            "assets": {name: {"sha256": "0"*64, "size": 1} for name in review.get("required_release_assets", [])},
            "updater_contract": {"install_locked": True},
        }
        validish_helper_manifest = mod.build_update_helper_manifest(
            release=None,
            staged_paths={
                mod.STABLE_EXE_ASSET: repo / "dist" / "Deimos.exe",
                mod.STABLE_CHECKSUM_ASSET: repo / "dist" / "Deimos.exe.sha256",
            },
            target_executable=repo / "Deimos.exe",
            rollback_directory=repo / "rollback",
            install_log=repo / "deimos-updater-helper.log",
            user_confirmed=False,
        )
        staged_review = {"checksum_status": "verified", "staged_files": ["Deimos.exe"]}
        dry_run = {"dry_run": True, "ok": True, "event": "dry_run_complete"}
        review2 = mod.build_install_unlock_gate_review(
            release_manifest=validish_release_manifest,
            helper_manifest=validish_helper_manifest,
            staged_review=staged_review,
            helper_dry_run=dry_run,
            user_confirmed=True,
        )
        if review2.get("install_unlocked") is not False:
            blockers.append("even satisfied design evidence must keep install_unlocked false in Phase 50")
    except Exception as exc:
        blockers.append(f"smoke exception: {exc}")
        review = {}
        review2 = {}

    report = {"phase": 50, "check": "install_unlock_gate_smoke", "ok": not blockers, "blockers": blockers, "empty_review": review, "evidence_review": review2}
    out = repo / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 1 if blockers else 0

if __name__ == "__main__":
    raise SystemExit(main())
