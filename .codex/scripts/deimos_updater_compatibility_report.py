#!/usr/bin/env python3
"""Validate updater-facing release manifest and checksum compatibility for Deimos releases."""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

EXPECTED_SHA_RE = re.compile(r"^[0-9a-f]{64}(?:\s+\*?Deimos\.exe)?$", re.I)
REQUIRED_MANIFEST_KEYS = ["application", "version", "created_utc", "artifacts", "release_requirements"]
REQUIRED_ARTIFACTS = {"Deimos.exe", "Deimos.exe.sha256"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict:
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
    dist = repo / "dist"
    exe = dist / "Deimos.exe"
    sha_file = dist / "Deimos.exe.sha256"
    manifest_file = dist / "release-manifest.json"
    blockers: list[str] = []
    warnings: list[str] = []
    artifacts: dict[str, object] = {
        "Deimos.exe": {"path": "dist/Deimos.exe", "exists": exe.exists()},
        "Deimos.exe.sha256": {"path": "dist/Deimos.exe.sha256", "exists": sha_file.exists()},
        "release-manifest.json": {"path": "dist/release-manifest.json", "exists": manifest_file.exists()},
    }
    if not exe.exists():
        if args.require_artifact:
            blockers.append("dist/Deimos.exe is required for updater compatibility validation")
        else:
            warnings.append("dist/Deimos.exe is absent; updater compatibility is in pre-build mode")
    else:
        digest = sha256(exe)
        artifacts["Deimos.exe"].update({"size_bytes": exe.stat().st_size, "sha256": digest})
        if not sha_file.exists():
            blockers.append("dist/Deimos.exe.sha256 is missing")
        else:
            sha_text = sha_file.read_text(encoding="utf-8", errors="ignore").strip()
            artifacts["Deimos.exe.sha256"].update({"text": sha_text, "format_valid": bool(EXPECTED_SHA_RE.match(sha_text)), "matches_exe": digest in sha_text})
            if not EXPECTED_SHA_RE.match(sha_text):
                blockers.append("dist/Deimos.exe.sha256 must be '<64-hex-sha256>  Deimos.exe' or '<64-hex-sha256>'")
            if digest not in sha_text:
                blockers.append("dist/Deimos.exe.sha256 does not match dist/Deimos.exe")
    if manifest_file.exists():
        manifest = read_json(manifest_file)
        missing_keys = [k for k in REQUIRED_MANIFEST_KEYS if k not in manifest]
        artifacts["release-manifest.json"].update({"manifest": manifest, "missing_keys": missing_keys})
        if missing_keys:
            blockers.append("release-manifest.json missing required keys: " + ", ".join(missing_keys))
        artifact_names = {a.get("name") for a in manifest.get("artifacts", []) if isinstance(a, dict)}
        missing_artifacts = sorted(REQUIRED_ARTIFACTS - artifact_names)
        if missing_artifacts:
            blockers.append("release-manifest.json missing required artifact records: " + ", ".join(missing_artifacts))
        reqs = set(manifest.get("release_requirements", [])) if isinstance(manifest.get("release_requirements", []), list) else set()
        for name in ["Deimos.exe", "Deimos.exe.sha256", "release-manifest.json"]:
            if name not in reqs:
                blockers.append(f"release-manifest.json release_requirements missing {name}")
        if manifest.get("application") != "Deimos":
            blockers.append("release-manifest.json application must be Deimos")
    else:
        if args.require_artifact:
            blockers.append("dist/release-manifest.json is missing")
        else:
            warnings.append("dist/release-manifest.json is absent; manifest validation is pre-build only")
    report = {
        "phase": 35,
        "mode": "post-build" if exe.exists() else "pre-build",
        "stable_asset_names": ["Deimos.exe", "Deimos.exe.sha256", "release-manifest.json"],
        "checksum_algorithm": "sha256",
        "checksum_file_contract": "<64-hex-sha256>  Deimos.exe",
        "artifacts": artifacts,
        "blockers": blockers,
        "warnings": warnings,
        "updater_compatible": not blockers,
    }
    if args.out:
        out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if blockers else 0

if __name__ == "__main__":
    raise SystemExit(main())
