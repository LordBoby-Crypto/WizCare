#!/usr/bin/env python3
"""Aggregate release asset contract and updater compatibility checks."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path


def run(cmd: list[str]) -> dict:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return {"cmd": cmd, "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"_load_error": str(e)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--require-artifact", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo)
    reports = repo / ".codex" / "reports"; reports.mkdir(parents=True, exist_ok=True)
    scripts = repo / ".codex" / "scripts"
    contract_path = reports / "phase35-release-asset-contract.json"
    updater_path = reports / "phase35-updater-compatibility.json"
    contract_cmd = [sys.executable, str(scripts / "deimos_release_asset_contract.py"), str(repo), str(contract_path)]
    updater_cmd = [sys.executable, str(scripts / "deimos_updater_compatibility_report.py"), str(repo), str(updater_path)]
    if args.require_artifact:
        updater_cmd.append("--require-artifact")
    subcommands = [run(contract_cmd), run(updater_cmd)]
    contract = load_json(contract_path)
    updater = load_json(updater_path)
    blockers: list[str] = []
    warnings: list[str] = []
    for report in (contract, updater):
        blockers.extend(report.get("blockers", []))
        warnings.extend(report.get("warnings", []))
    result = {
        "phase": 35,
        "release_asset_contract": contract,
        "updater_compatibility": updater,
        "subcommands": subcommands,
        "blockers": blockers,
        "warnings": warnings,
        "release_upload_safe": not blockers,
        "post_build_required_command": "python .codex/scripts/deimos_release_upload_safety.py . .codex/reports/phase35-release-upload-safety-postbuild.json --require-artifact",
    }
    if args.out:
        out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if blockers else 0

if __name__ == "__main__":
    raise SystemExit(main())
