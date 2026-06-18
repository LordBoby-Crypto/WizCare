#!/usr/bin/env python3
"""Validate that GitHub Actions formally build/check helper artifacts without enabling installs."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

WORKFLOWS = [
    ".github/workflows/build.yml",
    ".github/workflows/release.yml",
    ".github/workflows/develop.yml",
    ".github/workflows/ci.yml",
]
REQUIRED_SNIPPETS = [
    "libs/updater_helper",
    "deimos_updater_helper.spec",
    "deimos_update_helper_artifact_report.py",
    "deimos_phase46_helper_workflow_readiness.py",
]
HELPER_ASSETS = ["deimos-updater-helper.exe", "deimos-updater-helper.exe.sha256"]
FORBIDDEN = [
    "--install",
    "--replace",
    "--relaunch ",
    "deimos_updater_helper.py --manifest",
]

def inspect_workflow(path: Path) -> dict:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    lower = text.lower()
    missing = [s for s in REQUIRED_SNIPPETS if s not in text]
    helper_assets_present = {asset: asset in text for asset in HELPER_ASSETS}
    forbidden_hits = [f for f in FORBIDDEN if f.lower() in lower]
    build_step = "Build updater helper artifact" in text or "Build helper artifact" in text
    checksum_step = "Generate helper artifact checksum" in text or "deimos_update_helper_artifact_report.py" in text
    upload_step = all(helper_assets_present.values())
    return {
        "workflow": str(path),
        "exists": path.exists(),
        "build_step": build_step,
        "checksum_step": checksum_step,
        "helper_assets_present": helper_assets_present,
        "upload_step_or_package_includes_helper_assets": upload_step,
        "missing_required_snippets": missing,
        "forbidden_install_hits": forbidden_hits,
        "passed": path.exists() and not missing and not forbidden_hits,
    }

def run(repo: Path) -> dict:
    details = [inspect_workflow(repo / wf) for wf in WORKFLOWS]
    blockers = []
    warnings = []
    for d in details:
        if not d["exists"]:
            blockers.append(f"workflow missing: {d['workflow']}")
        if d["missing_required_snippets"]:
            blockers.append(f"workflow lacks helper build/check snippets: {d['workflow']}")
        if d["forbidden_install_hits"]:
            blockers.append(f"workflow contains forbidden helper install/relaunch behavior: {d['workflow']}")
        if not d["upload_step_or_package_includes_helper_assets"]:
            warnings.append(f"workflow does not expose both helper assets in package/upload path: {d['workflow']}")
    return {
        "phase": 46,
        "purpose": "helper release workflow integration",
        "helper_install_locked": True,
        "checked_workflows": details,
        "required_helper_assets": HELPER_ASSETS,
        "blockers": blockers,
        "warnings": warnings,
        "passed": not blockers,
    }

def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("repo", nargs="?", default=".")
    p.add_argument("output", nargs="?", default=".codex/reports/phase46-helper-workflow-integration.json")
    a = p.parse_args(argv)
    result = run(Path(a.repo).resolve())
    out = Path(a.output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["passed"] else 1
if __name__ == "__main__":
    raise SystemExit(main())
