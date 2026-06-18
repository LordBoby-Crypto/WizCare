#!/usr/bin/env python3
"""Phase 50 install unlock gate checker.

This checker intentionally reports install_locked=true. It exists to prevent a
future Codex/code change from enabling executable replacement before the full
manifest/helper/rollback/user-confirmation checklist is satisfied.
"""
from __future__ import annotations
from pathlib import Path
import argparse, json, sys

REQUIRED_SCRIPTS = [
    ".codex/scripts/deimos_fake_release_simulation.py",
    ".codex/scripts/deimos_release_manifest_postbuild_validation.py",
    ".codex/scripts/deimos_update_helper_scaffold_smoke.py",
    ".codex/scripts/deimos_update_helper_artifact_contract.py",
]
REQUIRED_SOURCE_MARKERS = {
    "src/update_system.py": [
        "build_install_unlock_gate_review",
        "install_unlocked",
        "install_locked",
        "helper_launch_locked",
        "automatic_install_locked",
    ],
    "src/gui/update_check.py": [
        "Review Install Design",
    ],
}
FORBIDDEN_GUI_MARKERS = [
    "subprocess.run([helper",
    "subprocess.Popen([helper",
    "deimos-updater-helper.exe",
    "os.replace(staged",
    "shutil.move(staged",
]


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as exc:
        return {"_json_error": str(exc)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("output", nargs="?", default=".codex/reports/phase50-install-unlock-gate.json")
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    blockers: list[str] = []
    warnings: list[str] = []

    for rel in REQUIRED_SCRIPTS:
        if not (repo / rel).exists():
            blockers.append(f"missing required prerequisite script: {rel}")

    for rel, markers in REQUIRED_SOURCE_MARKERS.items():
        path = repo / rel
        if not path.exists():
            blockers.append(f"missing required source: {rel}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        missing = [marker for marker in markers if marker not in text]
        if missing:
            blockers.append(f"{rel} missing markers: {', '.join(missing)}")

    gui = repo / "src/gui/update_check.py"
    if gui.exists():
        gui_text = gui.read_text(encoding="utf-8", errors="replace")
        found_forbidden = [m for m in FORBIDDEN_GUI_MARKERS if m in gui_text]
        if found_forbidden:
            blockers.append("GUI update code contains forbidden install/helper launch markers: " + ", ".join(found_forbidden))

    # Use optional previous simulation reports as evidence, but do not require them in a clean repo.
    sim_report = read_json(repo / ".codex/reports/phase49-release-simulation-readiness.json")
    if sim_report and not sim_report.get("ok", True):
        warnings.append("previous phase49 simulation report was not ok")

    report = {
        "phase": 50,
        "check": "install_unlock_gate",
        "install_unlocked": False,
        "install_locked": True,
        "helper_launch_locked": True,
        "automatic_install_locked": True,
        "blockers": blockers,
        "warnings": warnings,
        "required_before_unlock": [
            "real Windows helper executable build verified",
            "real post-build manifest includes Deimos.exe and helper artifact metadata",
            "staged review checksum_status verified",
            "helper dry-run succeeds against real staged artifacts",
            "rollback backup path and install log path are visible to user",
            "explicit final user confirmation dialog exists",
            "all lock-removal changes are reviewed in a separate phase",
        ],
    }
    out = repo / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 1 if blockers else 0

if __name__ == "__main__":
    raise SystemExit(main())
