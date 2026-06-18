#!/usr/bin/env python3
"""Validate the stable Deimos GitHub Release asset contract used by humans and future updaters."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

REQUIRED_RAW_ASSETS = ["dist/Deimos.exe", "dist/Deimos.exe.sha256", "dist/release-manifest.json"]
REQUIRED_RELEASE_FILES = ["Deimos.exe", "Deimos.exe.sha256", "release-manifest.json"]
WORKFLOW_DIR = Path(".github/workflows")


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def workflow_mentions_asset(body: str, asset: str) -> bool:
    normalized = body.replace('\\', '/')
    return asset in normalized


def find_release_upload_blocks(body: str) -> list[str]:
    blocks = []
    marker_positions = [m.start() for m in re.finditer(r"files:\s*\|", body)]
    for pos in marker_positions:
        blocks.append(body[pos:pos + 900])
    return blocks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("out", nargs="?")
    args = ap.parse_args()
    repo = Path(args.repo)
    blockers: list[str] = []
    warnings: list[str] = []
    workflows: dict[str, object] = {}
    workflow_dir = repo / WORKFLOW_DIR
    if not workflow_dir.exists():
        blockers.append(".github/workflows is missing")
    else:
        for wf in sorted(workflow_dir.glob("*.yml")) + sorted(workflow_dir.glob("*.yaml")):
            body = text(wf)
            info = {
                "uses_pyinstaller_spec": "Deimos.spec" in body,
                "runs_checksum_script": "deimos_checksum_release_artifacts.py" in body,
                "mentions_release_manifest": "dist/release-manifest.json" in body,
                "mentions_sha256": "dist/Deimos.exe.sha256" in body,
                "mentions_exe": "dist/Deimos.exe" in body,
                "release_upload_blocks": find_release_upload_blocks(body),
                "missing_required_raw_assets": [a for a in REQUIRED_RAW_ASSETS if not workflow_mentions_asset(body, a)],
            }
            workflows[str(wf.relative_to(repo))] = info
            if wf.name in {"build.yml", "release.yml", "develop.yml", "ci.yml"}:
                if not info["uses_pyinstaller_spec"]:
                    blockers.append(f"{wf.name} does not build with Deimos.spec")
                if not info["runs_checksum_script"]:
                    blockers.append(f"{wf.name} does not run deimos_checksum_release_artifacts.py")
                missing = info["missing_required_raw_assets"]
                if missing:
                    blockers.append(f"{wf.name} does not mention required release artifact(s): {', '.join(missing)}")
    # Check package/release copy contract in workflow text.
    combined = "\n".join(text(p) for p in workflow_dir.glob("*.y*ml")) if workflow_dir.exists() else ""
    for filename in REQUIRED_RELEASE_FILES:
        if filename not in combined:
            blockers.append(f"Release package contract missing {filename}")
    if "Deimos-${{ steps.version.outputs.VERSION_TAG }}.zip" not in combined and "Deimos-${{ steps.version.outputs.VERSION }}.zip" not in combined:
        warnings.append("Could not find a versioned Deimos-vX.Y.Z zip naming pattern in workflows")
    report = {
        "phase": 35,
        "required_raw_assets": REQUIRED_RAW_ASSETS,
        "required_release_files": REQUIRED_RELEASE_FILES,
        "workflows": workflows,
        "blockers": blockers,
        "warnings": warnings,
        "release_asset_contract_ready": not blockers,
    }
    if args.out:
        out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if blockers else 0

if __name__ == "__main__":
    raise SystemExit(main())
