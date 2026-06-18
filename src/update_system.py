"""Conservative GitHub release update helpers for Deimos.

This module is intentionally review-first. It can inspect GitHub release
metadata, select stable updater-facing assets, download files to a staging
directory, and verify SHA-256 checksums. It does not replace Deimos.exe,
restart the application, or launch a self-update helper.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib
import json
import re
import tempfile
import urllib.error
import urllib.request
import zipfile


DEFAULT_REPO = "Deimos-Wizard101/Deimos-Wizard101"
STABLE_EXE_ASSET = "Deimos.exe"
STABLE_CHECKSUM_ASSET = "Deimos.exe.sha256"
STABLE_MANIFEST_ASSET = "release-manifest.json"
USER_AGENT = "Deimos-Wizard101-update-check/1.0"


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    download_url: str
    size: int | None = None
    content_type: str | None = None


@dataclass(frozen=True)
class ReleaseInfo:
    tag_name: str
    name: str | None
    html_url: str | None
    prerelease: bool
    draft: bool
    assets: dict[str, ReleaseAsset]
    raw: dict[str, Any]

    def asset(self, name: str) -> ReleaseAsset | None:
        return self.assets.get(name)


@dataclass(frozen=True)
class UpdateCheckResult:
    current_version: str
    latest_version: str | None
    update_available: bool
    release: ReleaseInfo | None
    warnings: tuple[str, ...]


class UpdateSystemError(RuntimeError):
    """Raised when release update metadata or staged assets are invalid."""


def normalize_version(value: str) -> tuple[int, ...]:
    """Return a comparable numeric version tuple from common tag strings.

    Examples:
        "v3.13.1" -> (3, 13, 1)
        "3.14.0-dev" -> (3, 14, 0)
    """
    nums = re.findall(r"\d+", value or "")
    return tuple(int(n) for n in nums[:4]) or (0,)


def is_newer_version(latest: str, current: str) -> bool:
    return normalize_version(latest) > normalize_version(current)


def _request_json(url: str, timeout: float = 15.0) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise UpdateSystemError(f"GitHub returned HTTP {exc.code} for {url}") from exc
    except urllib.error.URLError as exc:
        raise UpdateSystemError(f"Could not reach GitHub release API: {exc.reason}") from exc


def parse_release(payload: dict[str, Any]) -> ReleaseInfo:
    assets: dict[str, ReleaseAsset] = {}
    for item in payload.get("assets") or []:
        name = str(item.get("name") or "")
        url = str(item.get("browser_download_url") or "")
        if not name or not url:
            continue
        assets[name] = ReleaseAsset(
            name=name,
            download_url=url,
            size=item.get("size"),
            content_type=item.get("content_type"),
        )
    return ReleaseInfo(
        tag_name=str(payload.get("tag_name") or ""),
        name=payload.get("name"),
        html_url=payload.get("html_url"),
        prerelease=bool(payload.get("prerelease")),
        draft=bool(payload.get("draft")),
        assets=assets,
        raw=payload,
    )


def get_latest_release(repo: str = DEFAULT_REPO, include_prereleases: bool = False) -> ReleaseInfo:
    if include_prereleases:
        payload = _request_json(f"https://api.github.com/repos/{repo}/releases")
        if not isinstance(payload, list):
            raise UpdateSystemError("Unexpected GitHub releases response")
        for release in payload:
            info = parse_release(release)
            if not info.draft:
                return info
        raise UpdateSystemError("No non-draft releases found")
    return parse_release(_request_json(f"https://api.github.com/repos/{repo}/releases/latest"))


def validate_release_assets(release: ReleaseInfo) -> tuple[str, ...]:
    warnings: list[str] = []
    if not release.tag_name:
        warnings.append("release is missing tag_name")
    for required in (STABLE_EXE_ASSET, STABLE_CHECKSUM_ASSET):
        if required not in release.assets:
            warnings.append(f"release is missing stable asset {required}")
    if STABLE_MANIFEST_ASSET not in release.assets:
        warnings.append(f"release is missing optional manifest asset {STABLE_MANIFEST_ASSET}")
    checksum = release.assets.get(STABLE_CHECKSUM_ASSET)
    if checksum and checksum.size is not None and checksum.size > 4096:
        warnings.append("checksum asset is unexpectedly large")
    return tuple(warnings)


def check_for_update(current_version: str, repo: str = DEFAULT_REPO, include_prereleases: bool = False) -> UpdateCheckResult:
    release = get_latest_release(repo=repo, include_prereleases=include_prereleases)
    warnings = list(validate_release_assets(release))
    latest = release.tag_name.lstrip("v") if release.tag_name else None
    return UpdateCheckResult(
        current_version=current_version,
        latest_version=latest,
        update_available=bool(latest and is_newer_version(latest, current_version)),
        release=release,
        warnings=tuple(warnings),
    )


def parse_sha256_checksum(text: str) -> str:
    first = text.strip().splitlines()[0] if text.strip() else ""
    match = re.match(r"^([a-fA-F0-9]{64})(?:\s+\*?Deimos\.exe)?\s*$", first)
    if not match:
        raise UpdateSystemError("checksum file must contain '<64-hex-sha256>  Deimos.exe'")
    return match.group(1).lower()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download_asset(asset: ReleaseAsset, destination: Path, timeout: float = 60.0) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(asset.download_url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp, destination.open("wb") as out:
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
    except urllib.error.URLError as exc:
        raise UpdateSystemError(f"Could not download {asset.name}: {exc.reason}") from exc
    return destination


def stage_release_assets(release: ReleaseInfo, stage_dir: Path | None = None) -> dict[str, Path]:
    """Download stable assets into a staging directory and verify checksum.

    This is intentionally non-installing. A caller must review the result and
    implement a separate, explicit install step if self-update is desired.
    """
    warnings = validate_release_assets(release)
    missing = [w for w in warnings if "missing stable asset" in w]
    if missing:
        raise UpdateSystemError("; ".join(missing))
    stage = Path(stage_dir) if stage_dir else Path(tempfile.mkdtemp(prefix="deimos-update-"))
    exe = download_asset(release.assets[STABLE_EXE_ASSET], stage / STABLE_EXE_ASSET)
    checksum_path = download_asset(release.assets[STABLE_CHECKSUM_ASSET], stage / STABLE_CHECKSUM_ASSET)
    expected = parse_sha256_checksum(checksum_path.read_text(encoding="utf-8"))
    actual = sha256_file(exe)
    if actual != expected:
        raise UpdateSystemError(f"checksum mismatch for {STABLE_EXE_ASSET}: expected {expected}, got {actual}")
    result = {STABLE_EXE_ASSET: exe, STABLE_CHECKSUM_ASSET: checksum_path}
    manifest_asset = release.assets.get(STABLE_MANIFEST_ASSET)
    if manifest_asset:
        result[STABLE_MANIFEST_ASSET] = download_asset(manifest_asset, stage / STABLE_MANIFEST_ASSET)
    return result



def _asset_size_from_path(path: Path | None) -> int | None:
    try:
        return path.stat().st_size if path and path.exists() else None
    except OSError:
        return None


def _read_manifest_json(path: Path | None) -> dict[str, Any] | None:
    if not path or not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"raw": data}
    except Exception as exc:
        return {"parse_error": str(exc)}


def build_staged_asset_review(release: ReleaseInfo, staged_paths: dict[str, Path | str]) -> dict[str, Any]:
    """Return review-only metadata for a staged update folder.

    This helper never installs, moves, replaces, executes, or relaunches files.
    It summarizes staged file presence, sizes, checksum status, and optional
    release-manifest contents so GUI/user review can happen before any future
    install flow is considered.
    """
    normalized: dict[str, Path] = {name: Path(path) for name, path in (staged_paths or {}).items()}
    exe_path = normalized.get(STABLE_EXE_ASSET)
    checksum_path = normalized.get(STABLE_CHECKSUM_ASSET)
    manifest_path = normalized.get(STABLE_MANIFEST_ASSET)
    checksum_status = "missing"
    expected_sha256 = None
    actual_sha256 = None
    if checksum_path and checksum_path.exists() and exe_path and exe_path.exists():
        try:
            expected_sha256 = parse_sha256_checksum(checksum_path.read_text(encoding="utf-8"))
            actual_sha256 = sha256_file(exe_path)
            checksum_status = "verified" if expected_sha256 == actual_sha256 else "mismatch"
        except Exception as exc:
            checksum_status = f"error: {exc}"
    assets: list[dict[str, Any]] = []
    for name in (STABLE_EXE_ASSET, STABLE_CHECKSUM_ASSET, STABLE_MANIFEST_ASSET):
        staged = normalized.get(name)
        release_asset = release.assets.get(name) if release else None
        assets.append({
            "name": name,
            "staged_path": str(staged) if staged else None,
            "present": bool(staged and staged.exists()),
            "staged_size": _asset_size_from_path(staged),
            "release_size": release_asset.size if release_asset else None,
            "download_url_present": bool(release_asset and release_asset.download_url),
        })
    return {
        "review_only": True,
        "install_locked": True,
        "release_tag": release.tag_name if release else None,
        "release_name": release.name if release else None,
        "release_url": release.html_url if release else None,
        "checksum_status": checksum_status,
        "expected_sha256": expected_sha256,
        "actual_sha256": actual_sha256,
        "assets": assets,
        "manifest": _read_manifest_json(manifest_path),
    }

# PHASE40_INSTALL_DESIGN_REVIEW
INSTALL_REVIEW_ONLY = True
INSTALL_ENABLED = False
INSTALL_HELPER_REQUIRED = True
INSTALL_HELPER_NAME = "deimos-updater-helper.exe"


def _path_exists(value: Path | str | None) -> bool:
    return bool(value and Path(value).exists())


def build_update_install_design_review(
    release: ReleaseInfo | None,
    staged_paths: dict[str, Path | str],
    current_executable: Path | str | None = None,
) -> dict[str, Any]:
    """Return a review-only install design report for a staged update.

    This function intentionally does not install, move, replace, execute,
    relaunch, spawn helper processes, or modify Deimos.exe. It documents what a
    future installer would need to prove before executable replacement could be
    considered.
    """
    staged_review = build_staged_asset_review(release, staged_paths)
    checksum_verified = staged_review.get("checksum_status") == "verified"
    exe_asset = next((a for a in staged_review.get("assets", []) if a.get("name") == STABLE_EXE_ASSET), {})
    exe_staged = bool(exe_asset.get("present"))
    blockers: list[str] = [
        "install flow is intentionally disabled in this build",
        "external helper process is not bundled or invoked by this design review",
    ]
    if not checksum_verified:
        blockers.append("staged Deimos.exe checksum is not verified")
    if not exe_staged:
        blockers.append("staged Deimos.exe is missing")

    return {
        "review_only": True,
        "install_enabled": False,
        "install_locked": True,
        "helper_required": INSTALL_HELPER_REQUIRED,
        "helper_name": INSTALL_HELPER_NAME,
        "current_executable_path": str(current_executable) if current_executable else None,
        "current_executable_exists": _path_exists(current_executable),
        "release_tag": release.tag_name if release else None,
        "checksum_verified": checksum_verified,
        "staged_exe_present": exe_staged,
        "blockers": blockers,
        "required_user_confirmations": [
            "confirm the staged release tag matches the intended release",
            "confirm checksum verification is successful",
            "confirm Deimos will close before replacement",
            "confirm rollback backup location before replacement",
            "confirm relaunch behavior explicitly",
        ],
        "required_helper_process_behaviors": [
            "wait for the current Deimos process to exit",
            "verify staged executable checksum again immediately before replacement",
            "copy current Deimos.exe to a timestamped rollback backup",
            "atomically replace Deimos.exe only after backup succeeds",
            "verify replacement file hash after copy/rename",
            "restore rollback backup if replacement verification fails",
            "write an install log next to the staged files",
            "relaunch Deimos only when the user explicitly requested it",
        ],
        "locked_file_handling_rules": [
            "never overwrite Deimos.exe while the process is running",
            "use an external helper process for replacement after GUI exit",
            "treat PermissionError and sharing violations as non-destructive blockers",
            "leave staged files intact when a lock prevents replacement",
        ],
        "rollback_rules": [
            "create rollback backup before any replacement attempt",
            "never delete rollback backup during the same install transaction",
            "restore backup if copied file hash does not match expected SHA-256",
            "surface rollback path to the user after install attempt",
        ],
        "explicitly_forbidden_in_gui_process": [
            "os.replace on the running executable",
            "subprocess launch of staged Deimos.exe as an installer",
            "silent update installation",
            "background startup installation",
            "deleting the current executable before backup is complete",
        ],
        "future_install_steps": [
            "bundle and verify a small updater helper executable",
            "add a signed/hashed helper contract",
            "add explicit install confirmation UI",
            "close Deimos and delegate replacement to the helper",
            "verify post-install executable hash and log result",
        ],
        "staged_asset_review": staged_review,
    }

# PHASE41_UPDATER_HELPER_SPECIFICATION
HELPER_SPEC_REVIEW_ONLY = True
HELPER_SPEC_VERSION = "1.0"
HELPER_MANIFEST_NAME = "deimos-helper-manifest.json"
HELPER_LOG_NAME = "deimos-updater-helper.log"
HELPER_ROLLBACK_DIR_NAME = "rollback"
HELPER_ALLOWED_EXIT_CODES = {
    0: "success",
    1: "invalid_arguments",
    2: "manifest_validation_failed",
    3: "source_checksum_failed",
    4: "target_process_still_running",
    5: "backup_failed",
    6: "replace_failed",
    7: "post_replace_hash_failed",
    8: "rollback_failed",
    9: "user_cancelled",
    10: "unexpected_error",
}


def build_update_helper_contract() -> dict[str, Any]:
    """Return the review-only contract for a future external updater helper.

    This does not launch a helper, install an update, replace files, or relaunch
    Deimos. It documents the exact helper interface that must be implemented and
    validated before install behavior can be added.
    """
    return {
        "review_only": True,
        "helper_enabled": False,
        "spec_version": HELPER_SPEC_VERSION,
        "helper_executable_name": INSTALL_HELPER_NAME,
        "manifest_name": HELPER_MANIFEST_NAME,
        "log_name": HELPER_LOG_NAME,
        "rollback_dir_name": HELPER_ROLLBACK_DIR_NAME,
        "required_cli_args": [
            "--manifest <path-to-deimos-helper-manifest.json>",
            "--wait-pid <current-deimos-process-id>",
            "--log <path-to-deimos-updater-helper.log>",
        ],
        "optional_cli_args": [
            "--relaunch <path-to-current-Deimos.exe>",
            "--dry-run",
            "--timeout-seconds <seconds>",
        ],
        "manifest_required_fields": [
            "schema_version",
            "release_tag",
            "target_executable",
            "staged_executable",
            "expected_sha256",
            "rollback_directory",
            "install_log",
            "created_at_utc",
            "user_confirmed",
        ],
        "exit_codes": HELPER_ALLOWED_EXIT_CODES,
        "required_helper_safety_rules": [
            "validate manifest schema before touching any executable",
            "wait for current Deimos process to exit before replacement",
            "verify staged executable SHA-256 before backup",
            "create rollback backup before replacement",
            "replace target executable only after backup succeeds",
            "verify target executable SHA-256 after replacement",
            "restore rollback backup if post-replacement verification fails",
            "write a structured install log for every attempt",
            "never delete staged files or rollback backup during the same transaction",
            "relaunch only when explicitly requested in CLI arguments",
        ],
        "forbidden_helper_behaviors": [
            "network downloads",
            "release selection",
            "silent install without user_confirmed true",
            "deleting rollback backups during install",
            "modifying files outside target executable, backup path, and log path",
        ],
    }


def build_update_helper_manifest(
    release: ReleaseInfo | None,
    staged_paths: dict[str, Path | str],
    target_executable: Path | str,
    rollback_directory: Path | str,
    install_log: Path | str,
    user_confirmed: bool = False,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    """Build a future-helper manifest without enabling helper execution."""
    staged_review = build_staged_asset_review(release, staged_paths)
    expected_sha256 = staged_review.get("expected_sha256")
    return {
        "schema_version": HELPER_SPEC_VERSION,
        "review_only": True,
        "helper_enabled": False,
        "release_tag": release.tag_name if release else None,
        "target_executable": str(target_executable),
        "staged_executable": str(Path(staged_paths.get(STABLE_EXE_ASSET, ""))) if staged_paths else "",
        "checksum_file": str(Path(staged_paths.get(STABLE_CHECKSUM_ASSET, ""))) if staged_paths else "",
        "expected_sha256": expected_sha256,
        "rollback_directory": str(rollback_directory),
        "install_log": str(install_log),
        "created_at_utc": created_at_utc,
        "user_confirmed": bool(user_confirmed),
        "install_locked": True,
        "staged_asset_review": staged_review,
        "helper_contract": build_update_helper_contract(),
    }


def validate_update_helper_manifest(manifest: dict[str, Any]) -> tuple[str, ...]:
    """Return manifest blockers for the future helper contract."""
    blockers: list[str] = []
    if not isinstance(manifest, dict):
        return ("manifest must be a JSON object",)
    required = build_update_helper_contract()["manifest_required_fields"]
    for field in required:
        if field not in manifest:
            blockers.append(f"manifest missing required field: {field}")
    if manifest.get("schema_version") != HELPER_SPEC_VERSION:
        blockers.append(f"manifest schema_version must be {HELPER_SPEC_VERSION}")
    if manifest.get("helper_enabled") is not False:
        blockers.append("helper_enabled must remain false until install implementation phase")
    if manifest.get("install_locked") is not True:
        blockers.append("install_locked must remain true during helper-spec phase")
    expected = manifest.get("expected_sha256")
    if expected is not None and not re.match(r"^[a-fA-F0-9]{64}$", str(expected)):
        blockers.append("expected_sha256 must be a 64-character hex string when present")
    if not manifest.get("target_executable"):
        blockers.append("target_executable must be set")
    if not manifest.get("staged_executable"):
        blockers.append("staged_executable must be set")
    if manifest.get("user_confirmed") is not True:
        blockers.append("user_confirmed must be true before a future helper may be launched")
    return tuple(blockers)

# PHASE44_HELPER_ARTIFACT_REVIEW
HELPER_EXECUTABLE_NAME = "deimos-updater-helper.exe"
HELPER_RELEASE_ASSET_NAME = "deimos-updater-helper.exe"
HELPER_RELEASE_CHECKSUM_ASSET_NAME = "deimos-updater-helper.exe.sha256"
HELPER_RELEASE_MANIFEST_FIELD = "updater_helper"

@dataclass(frozen=True)
class HelperArtifactReview:
    """Review-only status for a built updater helper artifact.

    This is intentionally not an install launcher. It only records whether a helper
    artifact exists, its size/hash, and whether the checksum file matches the
    stable release-artifact contract.
    """
    executable_path: str
    exists: bool
    size: int | None
    sha256: str | None
    checksum_path: str | None
    checksum_matches: bool | None
    install_locked: bool = True


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def parse_sha256_checksum_file(path: Path) -> tuple[str, str | None]:
    text = Path(path).read_text(encoding="utf-8").strip()
    parts = text.split()
    if not parts or not re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]):
        raise UpdateSystemError(f"Invalid SHA-256 checksum file: {path}")
    return parts[0].lower(), (parts[1] if len(parts) > 1 else None)


def review_helper_artifact(helper_path: str | Path, checksum_path: str | Path | None = None) -> HelperArtifactReview:
    helper = Path(helper_path)
    checksum = Path(checksum_path) if checksum_path else helper.with_suffix(helper.suffix + ".sha256")
    if not helper.exists():
        return HelperArtifactReview(str(helper), False, None, None, str(checksum), None)
    digest = sha256_file(helper)
    matches = None
    if checksum.exists():
        expected, filename = parse_sha256_checksum_file(checksum)
        matches = expected == digest and (filename in (None, helper.name, HELPER_EXECUTABLE_NAME))
    return HelperArtifactReview(str(helper), True, helper.stat().st_size, digest, str(checksum), matches)


INSTALL_UNLOCK_GATE_VERSION = "phase50-review-only"


def build_install_unlock_gate_review(
    *,
    helper_manifest: dict[str, Any] | None = None,
    release_manifest: dict[str, Any] | None = None,
    staged_review: dict[str, Any] | None = None,
    helper_dry_run: dict[str, Any] | None = None,
    user_confirmed: bool = False,
) -> dict[str, Any]:
    """Return the locked checklist required before real install code may exist.

    This is a design/review gate only. It does not install, move, replace,
    launch, relaunch, or delete anything. Future executable replacement work must
    satisfy every blocker here, then add a separate implementation phase with
    explicit user review.
    """
    required_release_assets = [
        STABLE_EXE_ASSET,
        STABLE_CHECKSUM_ASSET,
        STABLE_MANIFEST_ASSET,
        HELPER_EXECUTABLE_NAME,
        HELPER_RELEASE_CHECKSUM_ASSET_NAME,
    ]
    blockers: list[str] = []
    warnings: list[str] = []

    if not isinstance(release_manifest, dict):
        blockers.append("release_manifest is required before install can be considered")
    else:
        assets = release_manifest.get("assets") or {}
        missing_assets = [name for name in required_release_assets if name not in assets]
        if missing_assets:
            blockers.append("release_manifest missing required assets: " + ", ".join(missing_assets))
        contract = release_manifest.get("updater_contract") or {}
        if contract.get("install_locked") is not True:
            warnings.append("release_manifest should explicitly preserve install_locked=true until implementation phase")

    if not isinstance(helper_manifest, dict):
        blockers.append("helper_manifest is required before install can be considered")
    else:
        helper_blockers = validate_update_helper_manifest(helper_manifest)
        blockers.extend(f"helper_manifest: {b}" for b in helper_blockers)
        if helper_manifest.get("helper_enabled") is not False:
            blockers.append("helper_manifest helper_enabled must remain false until install implementation phase")
        if helper_manifest.get("install_locked") is not True:
            blockers.append("helper_manifest install_locked must remain true until install implementation phase")

    if not isinstance(staged_review, dict):
        blockers.append("staged_review is required before install can be considered")
    else:
        status = str(staged_review.get("checksum_status") or "").lower()
        if status not in {"verified", "ok", "passed"}:
            blockers.append("staged_review checksum_status must be verified")
        if not staged_review.get("staged_files"):
            blockers.append("staged_review must list staged_files")

    if not isinstance(helper_dry_run, dict):
        blockers.append("helper_dry_run result is required before install can be considered")
    else:
        if helper_dry_run.get("dry_run") is not True:
            blockers.append("helper_dry_run must be a dry-run result")
        if helper_dry_run.get("ok") is not True:
            blockers.append("helper_dry_run must be ok=true")
        if "dry_run_complete" not in str(helper_dry_run.get("event") or helper_dry_run.get("status") or ""):
            warnings.append("helper_dry_run should contain a dry_run_complete event/status")

    if user_confirmed:
        warnings.append("user_confirmed is ignored in Phase 50; real install remains locked")

    required_future_work = [
        "compile and verify deimos-updater-helper.exe on Windows",
        "prove helper dry-run with real built artifacts and release-manifest.json",
        "add explicit final confirmation dialog with release tag, hashes, rollback path, and target exe",
        "write rollback backup before replacing any executable",
        "verify post-install executable hash before relaunch",
        "surface helper exit code and log path to the user",
        "keep startup/background install disabled unless a separate future phase approves it",
    ]

    return {
        "phase": 50,
        "gate_version": INSTALL_UNLOCK_GATE_VERSION,
        "install_unlocked": False,
        "install_locked": True,
        "helper_launch_locked": True,
        "automatic_install_locked": True,
        "blockers": blockers,
        "warnings": warnings,
        "required_release_assets": required_release_assets,
        "required_future_work": required_future_work,
        "forbidden_until_unlocked": [
            "launching deimos-updater-helper.exe from GUI",
            "moving staged Deimos.exe over the running executable",
            "relaunching Deimos automatically",
            "deleting rollback backups during the same install transaction",
            "silent/background update installation",
        ],
    }



# PHASE56_HELPER_DRY_RUN_LOG_DETECTION
HELPER_DRY_RUN_REQUIRED_EVENTS = ("manifest_loaded", "checksum_verified", "dry_run_complete")


def classify_helper_dry_run_log(log_status: str, log_events: list[dict[str, Any]]) -> dict[str, Any]:
    """Classify helper dry-run log status for GUI review.

    Returns one of: missing, invalid, incomplete, valid. This is review-only
    and never launches helper or install behavior.
    """
    if not log_status or str(log_status).startswith("missing"):
        return {
            "status": "missing",
            "valid": False,
            "missing_events": list(HELPER_DRY_RUN_REQUIRED_EVENTS),
            "invalid_entries": [],
            "message": "No helper dry-run log was found in the staged folder.",
        }
    if str(log_status).startswith("error"):
        return {
            "status": "invalid",
            "valid": False,
            "missing_events": list(HELPER_DRY_RUN_REQUIRED_EVENTS),
            "invalid_entries": [log_status],
            "message": "Helper dry-run log could not be read.",
        }
    invalid_entries: list[Any] = []
    event_names: set[str] = set()
    for event in log_events or []:
        if not isinstance(event, dict):
            invalid_entries.append(event)
            continue
        if "raw" in event and "event" not in event:
            invalid_entries.append(event.get("raw"))
            continue
        name = event.get("event") or event.get("status")
        if name:
            event_names.add(str(name))
    if invalid_entries:
        return {
            "status": "invalid",
            "valid": False,
            "missing_events": [e for e in HELPER_DRY_RUN_REQUIRED_EVENTS if e not in event_names],
            "invalid_entries": invalid_entries[:10],
            "message": "Helper dry-run log contains invalid/non-JSONL entries.",
        }
    missing_events = [event for event in HELPER_DRY_RUN_REQUIRED_EVENTS if event not in event_names]
    if missing_events:
        return {
            "status": "incomplete",
            "valid": False,
            "missing_events": missing_events,
            "invalid_entries": [],
            "message": "Helper dry-run log is present but incomplete.",
        }
    return {
        "status": "valid",
        "valid": True,
        "missing_events": [],
        "invalid_entries": [],
        "message": "Helper dry-run log is valid and complete.",
    }

# PHASE54_HELPER_DRY_RUN_GUI_REVIEW
HELPER_DRY_RUN_GUI_REVIEW_ONLY = True

def build_helper_dry_run_review(
    release: ReleaseInfo | None,
    staged_paths: dict[str, Path | str],
    current_executable: Path | str | None = None,
    helper_log: Path | str | None = None,
) -> dict[str, Any]:
    """Build a GUI-safe helper dry-run review report.

    This function never launches the helper, installs, replaces, relaunches, or
    modifies Deimos.exe. It summarizes what a helper dry-run would need, shows
    the generated manifest fields, and optionally reads an existing helper dry-run
    log if one was produced by a separate test harness.
    """
    staged_review = build_staged_asset_review(release, staged_paths)
    stage_root = None
    if staged_paths:
        first_path = next(iter(staged_paths.values()), None)
        if first_path:
            stage_root = Path(first_path).parent
    log_path = Path(helper_log) if helper_log else (stage_root / HELPER_LOG_NAME if stage_root else None)
    rollback_dir = stage_root / HELPER_ROLLBACK_DIR_NAME if stage_root else Path(HELPER_ROLLBACK_DIR_NAME)
    target = Path(current_executable) if current_executable else Path(STABLE_EXE_ASSET)
    manifest = build_update_helper_manifest(
        release=release,
        staged_paths=staged_paths,
        target_executable=target,
        rollback_directory=rollback_dir,
        install_log=log_path or Path(HELPER_LOG_NAME),
        user_confirmed=False,
    )
    manifest_blockers = list(validate_update_helper_manifest(manifest))
    # In GUI dry-run review, user_confirmed=false is expected because no install can be launched.
    manifest_blockers_for_review = [b for b in manifest_blockers if b != "user_confirmed must be true before a future helper may be launched"]
    helper_command_preview = [
        INSTALL_HELPER_NAME,
        "--manifest",
        str((stage_root / HELPER_MANIFEST_NAME) if stage_root else HELPER_MANIFEST_NAME),
        "--wait-pid",
        "<current-deimos-pid>",
        "--log",
        str(log_path or HELPER_LOG_NAME),
        "--dry-run",
    ]
    log_events: list[dict[str, Any]] = []
    log_status = "missing"
    if log_path and log_path.exists():
        log_status = "present"
        try:
            for line in log_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                    log_events.append(event if isinstance(event, dict) else {"raw": event})
                except json.JSONDecodeError:
                    log_events.append({"raw": line})
        except Exception as exc:
            log_status = f"error: {exc}"
    log_review = classify_helper_dry_run_log(log_status, log_events)
    return {
        "review_only": True,
        "helper_launch_enabled": False,
        "install_execution_enabled": False,
        "non_dry_run_enabled": False,
        "release_tag": release.tag_name if release else None,
        "checksum_status": staged_review.get("checksum_status"),
        "staged_exe_present": any(a.get("name") == STABLE_EXE_ASSET and a.get("present") for a in staged_review.get("assets", [])),
        "helper_name": INSTALL_HELPER_NAME,
        "helper_command_preview": helper_command_preview,
        "manifest_preview": manifest,
        "manifest_blockers_for_review": manifest_blockers_for_review,
        "helper_log_path": str(log_path) if log_path else None,
        "helper_log_status": log_review["status"],
        "helper_log_raw_status": log_status,
        "helper_log_valid": log_review["valid"],
        "helper_log_missing_events": log_review["missing_events"],
        "helper_log_invalid_entries": log_review["invalid_entries"],
        "helper_log_message": log_review["message"],
        "helper_log_events": log_events,
        "dry_run_required_events": list(HELPER_DRY_RUN_REQUIRED_EVENTS),
        "locked_actions": [
            "launching the helper from the GUI",
            "non-dry-run helper execution",
            "replacing Deimos.exe",
            "relaunching Deimos",
            "automatic installation",
        ],
        "staged_asset_review": staged_review,
    }


# PHASE57_STAGED_UPDATE_UX_REPORT_POLISH
STAGED_UX_REPORT_VERSION = "1.0"


def _phase57_status_label(value: Any) -> str:
    value = "unknown" if value is None else str(value)
    return value.replace("_", " ").strip() or "unknown"


def build_staged_update_ux_summary(
    release: ReleaseInfo | None,
    staged_paths: dict[str, Path | str],
    current_executable: Path | str | None = None,
) -> dict[str, Any]:
    """Build display-focused staged-update UX status without installing anything.

    This report is intentionally read-only. It condenses checksum, manifest,
    helper dry-run log, and install-lock states into a user-facing summary that
    can be displayed by the GUI or written to Codex reports.
    """
    staged_review = build_staged_asset_review(release, staged_paths)
    helper_review = build_helper_dry_run_review(
        release=release,
        staged_paths=staged_paths,
        current_executable=current_executable,
    )
    install_design = build_update_install_design_review(
        release=release,
        staged_paths=staged_paths,
        current_executable=current_executable,
    )

    checksum_status = str(staged_review.get("checksum_status") or "missing")
    manifest = staged_review.get("manifest")
    manifest_status = "present"
    if manifest is None:
        manifest_status = "missing"
    elif isinstance(manifest, dict) and manifest.get("parse_error"):
        manifest_status = "invalid"

    assets = staged_review.get("assets") or []
    missing_assets = [a.get("name") for a in assets if not a.get("present")]
    present_assets = [a.get("name") for a in assets if a.get("present")]
    helper_log_status = str(helper_review.get("helper_log_status") or "missing")
    install_locked = bool(install_design.get("install_locked", True))

    blockers: list[str] = []
    if checksum_status != "verified":
        blockers.append(f"checksum status is {checksum_status}")
    if STABLE_EXE_ASSET in missing_assets:
        blockers.append("staged Deimos.exe is missing")
    if STABLE_CHECKSUM_ASSET in missing_assets:
        blockers.append("staged checksum file is missing")
    if helper_log_status != "valid":
        blockers.append(f"helper dry-run log status is {helper_log_status}")
    if not install_locked:
        blockers.append("install lock unexpectedly disabled")

    if checksum_status == "verified" and helper_log_status == "valid" and install_locked:
        headline = "Staged update is verified and review-only. Installation remains locked."
        severity = "ready_for_review"
    elif checksum_status == "verified" and install_locked:
        headline = "Staged update checksum is verified; helper dry-run review still needs attention."
        severity = "needs_helper_review"
    else:
        headline = "Staged update needs attention before it should be trusted."
        severity = "needs_attention"

    summary_lines = [
        headline,
        f"Release tag: {release.tag_name if release else 'unknown'}",
        f"Checksum: {_phase57_status_label(checksum_status)}",
        f"Manifest: {_phase57_status_label(manifest_status)}",
        f"Helper dry-run log: {_phase57_status_label(helper_log_status)}",
        "Install execution: locked" if install_locked else "Install execution: unlocked unexpectedly",
    ]
    if missing_assets:
        summary_lines.append("Missing staged assets: " + ", ".join(str(a) for a in missing_assets))
    if blockers:
        summary_lines.append("Attention needed: " + "; ".join(blockers))

    return {
        "review_only": True,
        "version": STAGED_UX_REPORT_VERSION,
        "severity": severity,
        "headline": headline,
        "summary_lines": summary_lines,
        "release_tag": release.tag_name if release else None,
        "checksum_status": checksum_status,
        "manifest_status": manifest_status,
        "helper_log_status": helper_log_status,
        "install_locked": install_locked,
        "present_assets": present_assets,
        "missing_assets": missing_assets,
        "blockers": blockers,
        "staged_asset_review": staged_review,
        "helper_dry_run_review": helper_review,
        "install_design_review": install_design,
    }


# PHASE58_STAGED_UPDATE_PROBLEM_RESOLUTION
STAGED_PROBLEM_RESOLUTION_VERSION = "1.0"


def _phase58_problem(code: str, severity: str, title: str, explanation: str, next_steps: list[str]) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "title": title,
        "explanation": explanation,
        "next_steps": next_steps,
    }


def build_staged_update_problem_resolution_guidance(
    release: ReleaseInfo | None,
    staged_paths: dict[str, Path | str],
    current_executable: Path | str | None = None,
) -> dict[str, Any]:
    """Return user-facing next steps for staged update problem states.

    This is display/report guidance only. It never downloads, installs, launches
    helpers, replaces Deimos.exe, relaunches Deimos, or mutates staged files.
    """
    ux = build_staged_update_ux_summary(
        release=release,
        staged_paths=staged_paths,
        current_executable=current_executable,
    )
    staged_review = ux.get("staged_asset_review") or {}
    helper_review = ux.get("helper_dry_run_review") or {}
    install_design = ux.get("install_design_review") or {}
    assets = staged_review.get("assets") or []
    asset_by_name = {asset.get("name"): asset for asset in assets}
    problems: list[dict[str, Any]] = []

    exe_asset = asset_by_name.get(STABLE_EXE_ASSET, {})
    checksum_asset = asset_by_name.get(STABLE_CHECKSUM_ASSET, {})
    manifest_asset = asset_by_name.get(STABLE_MANIFEST_ASSET, {})

    if not exe_asset.get("present"):
        problems.append(_phase58_problem(
            "missing_staged_executable",
            "blocker",
            "Deimos.exe is missing from the staging folder.",
            "The staged update cannot be trusted because the primary executable was not staged.",
            [
                "Run the staged download flow again.",
                "Confirm the GitHub release includes the stable Deimos.exe asset.",
                "Do not attempt any install design review until Deimos.exe is present.",
            ],
        ))

    if not checksum_asset.get("present"):
        problems.append(_phase58_problem(
            "missing_checksum_file",
            "blocker",
            "Deimos.exe.sha256 is missing from the staging folder.",
            "The staged executable cannot be verified without the checksum file.",
            [
                "Run the staged download flow again.",
                "Confirm the release uploaded Deimos.exe.sha256 using the stable asset name.",
                "Do not trust the staged executable until checksum verification succeeds.",
            ],
        ))

    checksum_status = str(staged_review.get("checksum_status") or "missing")
    if checksum_status == "mismatch":
        problems.append(_phase58_problem(
            "checksum_mismatch",
            "blocker",
            "Checksum verification failed.",
            "The staged Deimos.exe hash does not match Deimos.exe.sha256.",
            [
                "Delete the staged folder and download the assets again.",
                "If the mismatch repeats, treat the release as invalid and rebuild/re-upload release assets.",
                "Do not run helper dry-run or install review from this staging folder.",
            ],
        ))
    elif checksum_status.startswith("error"):
        problems.append(_phase58_problem(
            "checksum_parse_or_read_error",
            "blocker",
            "Checksum verification could not be completed.",
            checksum_status,
            [
                "Inspect Deimos.exe.sha256 and confirm it uses '<64-hex-sha256>  Deimos.exe'.",
                "Regenerate the checksum from a trusted build if the file is malformed.",
                "Run the staged download flow again after fixing the release asset.",
            ],
        ))
    elif checksum_status in {"missing", "unknown"} and (exe_asset.get("present") or checksum_asset.get("present")):
        problems.append(_phase58_problem(
            "checksum_not_verified",
            "warning",
            "Checksum is not verified yet.",
            "The staging folder exists, but the review could not prove Deimos.exe integrity.",
            [
                "Confirm both Deimos.exe and Deimos.exe.sha256 are present.",
                "Run the staged asset review/checksum report again.",
                "Keep install behavior locked until the checksum status is verified.",
            ],
        ))

    manifest = staged_review.get("manifest")
    manifest_status = ux.get("manifest_status") or "unknown"
    if not manifest_asset.get("present"):
        problems.append(_phase58_problem(
            "missing_release_manifest",
            "warning",
            "release-manifest.json is missing from the staging folder.",
            "The executable can still be checksum-verified, but the richer release manifest review is unavailable.",
            [
                "Confirm the release workflow uploaded release-manifest.json.",
                "Regenerate the release manifest during the release build if missing.",
                "Use checksum and asset-name checks as the minimum trust gate until a manifest is available.",
            ],
        ))
    elif isinstance(manifest, dict) and manifest.get("parse_error"):
        problems.append(_phase58_problem(
            "invalid_release_manifest",
            "warning",
            "release-manifest.json could not be parsed.",
            str(manifest.get("parse_error")),
            [
                "Open release-manifest.json and confirm it is valid JSON.",
                "Regenerate it with the release checksum script.",
                "Keep the manifest review marked invalid until parsing succeeds.",
            ],
        ))

    helper_status = str(helper_review.get("helper_log_status") or "missing")
    if helper_status == "missing":
        problems.append(_phase58_problem(
            "missing_helper_dry_run_log",
            "warning",
            "Helper dry-run log is missing.",
            "No helper dry-run log was found in the staged folder, so the helper pathway has not been simulated for this staged update.",
            [
                "Run .codex/scripts/deimos_helper_dryrun_log_generator.py against the staging folder.",
                "Reopen the staged update review after the log is generated.",
                "Keep helper launch and install behavior locked.",
            ],
        ))
    elif helper_status == "invalid":
        problems.append(_phase58_problem(
            "invalid_helper_dry_run_log",
            "warning",
            "Helper dry-run log has invalid entries.",
            "The staged helper log contains non-JSONL or malformed entries.",
            [
                "Regenerate the helper dry-run log from the staged folder.",
                "Inspect invalid log entries before trusting the dry-run report.",
                "Keep install behavior locked until the log is valid.",
            ],
        ))
    elif helper_status == "incomplete":
        missing_events = helper_review.get("helper_log_missing_events") or []
        problems.append(_phase58_problem(
            "incomplete_helper_dry_run_log",
            "warning",
            "Helper dry-run log is incomplete.",
            "The log is readable, but it is missing required events: " + ", ".join(str(e) for e in missing_events),
            [
                "Regenerate the helper dry-run log from the staged folder.",
                "Confirm the log includes plan_built, checksum_verified, and dry_run_complete.",
                "Do not use the log as a readiness signal until all required events are present.",
            ],
        ))

    if install_design.get("install_locked", True):
        problems.append(_phase58_problem(
            "install_locked_by_design",
            "info",
            "Install execution is locked by design.",
            "This build supports review, staging, checksum verification, and dry-run inspection only.",
            [
                "Use the review dialogs to inspect staged files and helper dry-run status.",
                "Do not expect an Install button in this build.",
                "Future install work must pass the install unlock gate before enabling executable replacement.",
            ],
        ))
    else:
        problems.append(_phase58_problem(
            "install_lock_unexpectedly_disabled",
            "blocker",
            "Install execution appears to be unlocked unexpectedly.",
            "The safety model requires install behavior to remain disabled in this phase.",
            [
                "Treat this as a release blocker.",
                "Run the Phase 50 install unlock gate checker.",
                "Do not publish this build until install lock behavior is restored.",
            ],
        ))

    blockers = [p for p in problems if p["severity"] == "blocker"]
    warnings = [p for p in problems if p["severity"] == "warning"]
    headline = "Staged update guidance is available."
    if blockers:
        headline = "Staged update has blocker problems to resolve."
    elif warnings:
        headline = "Staged update is reviewable but has warnings to resolve."
    elif checksum_status == "verified" and helper_status == "valid":
        headline = "Staged update is verified for review; install remains locked."

    return {
        "review_only": True,
        "version": STAGED_PROBLEM_RESOLUTION_VERSION,
        "headline": headline,
        "problem_count": len(problems),
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "info_count": len([p for p in problems if p["severity"] == "info"]),
        "problems": problems,
        "checksum_status": checksum_status,
        "manifest_status": manifest_status,
        "helper_log_status": helper_status,
        "install_locked": bool(install_design.get("install_locked", True)),
        "summary": ux,
    }


# PHASE59_STAGED_UPDATE_SELF_DIAGNOSTICS_EXPORT
STAGED_DIAGNOSTICS_VERSION = "1.0"
STAGED_DIAGNOSTICS_FILENAME = "deimos-staged-update-diagnostics.json"


def build_staged_update_diagnostics_bundle(
    release: ReleaseInfo | None,
    staged_paths: dict[str, Path | str],
    current_executable: Path | str | None = None,
) -> dict[str, Any]:
    """Build a single review-only diagnostics object for staged update issues.

    This never downloads, installs, launches helpers, replaces Deimos.exe,
    relaunches Deimos, or mutates staged files. It aggregates the staged asset
    review, UX summary, problem-resolution guidance, helper dry-run log review,
    and install-lock/design status for export or support/debug review.
    """
    normalized = {str(name): str(Path(path)) for name, path in (staged_paths or {}).items()}
    staged_review = build_staged_asset_review(release, staged_paths or {})
    helper_review = build_helper_dry_run_review(release, staged_paths or {}, current_executable=current_executable)
    install_design = build_update_install_design_review(release, staged_paths or {}, current_executable=current_executable)
    ux_summary = build_staged_update_ux_summary(release, staged_paths or {}, current_executable=current_executable)
    guidance = build_staged_update_problem_resolution_guidance(release, staged_paths or {}, current_executable=current_executable)
    return {
        "review_only": True,
        "version": STAGED_DIAGNOSTICS_VERSION,
        "install_locked": True,
        "helper_launch_from_gui_enabled": False,
        "install_execution_enabled": False,
        "non_dry_run_enabled": False,
        "real_install_attempted": False,
        "release": {
            "tag_name": release.tag_name if release else None,
            "name": release.name if release else None,
            "html_url": release.html_url if release else None,
            "prerelease": release.prerelease if release else None,
            "draft": release.draft if release else None,
        },
        "staged_paths": normalized,
        "current_executable": str(current_executable) if current_executable else None,
        "staged_asset_review": staged_review,
        "helper_dry_run_review": helper_review,
        "install_design_review": install_design,
        "ux_summary": ux_summary,
        "problem_resolution_guidance": guidance,
        "summary": {
            "headline": guidance.get("headline") or ux_summary.get("headline"),
            "checksum_status": staged_review.get("checksum_status"),
            "helper_log_status": helper_review.get("helper_log_status"),
            "manifest_status": ux_summary.get("manifest_status"),
            "problem_count": guidance.get("problem_count"),
            "blocker_count": guidance.get("blocker_count"),
            "warning_count": guidance.get("warning_count"),
            "install_locked": True,
        },
    }


def export_staged_update_diagnostics_bundle(
    release: ReleaseInfo | None,
    staged_paths: dict[str, Path | str],
    output_zip: Path | str,
    current_executable: Path | str | None = None,
) -> Path:
    """Write a self-contained staged update diagnostics ZIP.

    The bundle contains JSON diagnostics and, when present, copies of the small
    review artifacts: checksum file, release manifest, helper manifest, and
    helper dry-run log. It intentionally excludes Deimos.exe and any executable
    payloads so the diagnostics bundle is safe to share.
    """
    out = Path(output_zip)
    out.parent.mkdir(parents=True, exist_ok=True)
    diagnostics = build_staged_update_diagnostics_bundle(release, staged_paths or {}, current_executable=current_executable)
    staged_dir = None
    exe_path = staged_paths.get(STABLE_EXE_ASSET) if staged_paths else None
    if exe_path:
        staged_dir = Path(exe_path).parent
    safe_artifacts = []
    for name in (STABLE_CHECKSUM_ASSET, STABLE_MANIFEST_ASSET, HELPER_MANIFEST_NAME, HELPER_LOG_NAME):
        direct = Path(staged_paths.get(name, "")) if staged_paths and staged_paths.get(name) else None
        candidate = direct if direct and direct.exists() else (staged_dir / name if staged_dir else None)
        if candidate and candidate.exists() and candidate.is_file():
            safe_artifacts.append((name, candidate))
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(STAGED_DIAGNOSTICS_FILENAME, json.dumps(diagnostics, indent=2, sort_keys=True))
        zf.writestr("README.txt", "Deimos staged update diagnostics bundle. Review-only; contains no executable payloads.\n")
        for name, path in safe_artifacts:
            zf.write(path, f"artifacts/{name}")
    return out


# PHASE60_61_STAGED_UPDATE_DIAGNOSTICS_IMPORT_AND_COMPARISON
STAGED_DIAGNOSTICS_IMPORT_VERSION = "1.0"
STAGED_DIAGNOSTICS_COMPARISON_VERSION = "1.0"
UNSAFE_DIAGNOSTICS_SUFFIXES = (".exe", ".dll", ".msi", ".bat", ".cmd", ".ps1")
REQUIRED_DIAGNOSTICS_MEMBERS = (STAGED_DIAGNOSTICS_FILENAME, "README.txt")
OPTIONAL_SAFE_DIAGNOSTICS_MEMBERS = (
    f"artifacts/{STABLE_CHECKSUM_ASSET}",
    f"artifacts/{STABLE_MANIFEST_ASSET}",
    f"artifacts/{HELPER_MANIFEST_NAME}",
    f"artifacts/{HELPER_LOG_NAME}",
)


def _diagnostics_member_is_unsafe(name: str) -> bool:
    normalized = str(name).replace("\\", "/").lower().lstrip("/")
    return any(normalized.endswith(suffix) for suffix in UNSAFE_DIAGNOSTICS_SUFFIXES)


def import_staged_update_diagnostics_bundle(bundle_zip: Path | str) -> dict[str, Any]:
    """Read a staged-update diagnostics ZIP in review-only mode.

    The importer rejects bundles that include executable payloads, require the
    diagnostics JSON file, and returns a compact summary for GUI/support review.
    It does not execute files, stage updates, launch helpers, install updates,
    replace Deimos.exe, or relaunch the app.
    """
    bundle = Path(bundle_zip)
    result: dict[str, Any] = {
        "review_only": True,
        "version": STAGED_DIAGNOSTICS_IMPORT_VERSION,
        "bundle_path": str(bundle),
        "safe_bundle": False,
        "valid": False,
        "errors": [],
        "warnings": [],
        "members": [],
        "unsafe_members": [],
        "missing_required_members": [],
        "diagnostics": None,
        "summary": {},
        "install_execution_enabled": False,
        "helper_launch_from_gui_enabled": False,
        "non_dry_run_enabled": False,
        "real_install_attempted": False,
    }
    if not bundle.exists():
        result["errors"].append("diagnostics_bundle_missing")
        return result
    if not zipfile.is_zipfile(bundle):
        result["errors"].append("diagnostics_bundle_not_zip")
        return result
    try:
        with zipfile.ZipFile(bundle, "r") as zf:
            members = [info.filename for info in zf.infolist() if not info.is_dir()]
            result["members"] = members
            unsafe = [name for name in members if _diagnostics_member_is_unsafe(name)]
            result["unsafe_members"] = unsafe
            if unsafe:
                result["errors"].append("diagnostics_bundle_contains_executable_payload")
                return result
            missing = [name for name in REQUIRED_DIAGNOSTICS_MEMBERS if name not in members]
            result["missing_required_members"] = missing
            if missing:
                result["errors"].append("diagnostics_bundle_missing_required_members")
                return result
            raw = zf.read(STAGED_DIAGNOSTICS_FILENAME).decode("utf-8")
            diagnostics = json.loads(raw)
    except (OSError, zipfile.BadZipFile, UnicodeDecodeError, json.JSONDecodeError) as exc:
        result["errors"].append(f"diagnostics_bundle_read_failed:{type(exc).__name__}")
        return result

    summary = diagnostics.get("summary", {}) if isinstance(diagnostics, dict) else {}
    if not isinstance(diagnostics, dict):
        result["errors"].append("diagnostics_json_not_object")
        return result
    if diagnostics.get("review_only") is not True:
        result["warnings"].append("diagnostics_review_only_flag_missing_or_false")
    lock_fields = {
        "install_locked": bool(diagnostics.get("install_locked", True)),
        "install_execution_enabled": bool(diagnostics.get("install_execution_enabled", False)),
        "helper_launch_from_gui_enabled": bool(diagnostics.get("helper_launch_from_gui_enabled", False)),
        "non_dry_run_enabled": bool(diagnostics.get("non_dry_run_enabled", False)),
        "real_install_attempted": bool(diagnostics.get("real_install_attempted", False)),
    }
    if lock_fields["install_execution_enabled"] or lock_fields["helper_launch_from_gui_enabled"] or lock_fields["non_dry_run_enabled"] or lock_fields["real_install_attempted"]:
        result["errors"].append("diagnostics_lock_state_unsafe")
        result["diagnostics"] = diagnostics
        result["summary"] = summary
        return result
    result["diagnostics"] = diagnostics
    result["summary"] = {
        "headline": summary.get("headline"),
        "checksum_status": summary.get("checksum_status"),
        "manifest_status": summary.get("manifest_status"),
        "helper_log_status": summary.get("helper_log_status"),
        "problem_count": summary.get("problem_count"),
        "blocker_count": summary.get("blocker_count"),
        "warning_count": summary.get("warning_count"),
        **lock_fields,
    }
    result["safe_bundle"] = True
    result["valid"] = True
    return result


def compare_staged_update_diagnostics_bundles(left_bundle: Path | str, right_bundle: Path | str) -> dict[str, Any]:
    """Compare two safe staged-update diagnostics bundles in read-only mode."""
    left = import_staged_update_diagnostics_bundle(left_bundle)
    right = import_staged_update_diagnostics_bundle(right_bundle)
    report: dict[str, Any] = {
        "review_only": True,
        "version": STAGED_DIAGNOSTICS_COMPARISON_VERSION,
        "valid": bool(left.get("valid") and right.get("valid")),
        "left": {"path": str(left_bundle), "valid": left.get("valid"), "errors": left.get("errors", [])},
        "right": {"path": str(right_bundle), "valid": right.get("valid"), "errors": right.get("errors", [])},
        "differences": [],
        "changed_fields": [],
        "install_execution_enabled": False,
        "helper_launch_from_gui_enabled": False,
        "non_dry_run_enabled": False,
        "real_install_attempted": False,
    }
    if not report["valid"]:
        report["differences"].append({
            "field": "bundle_validity",
            "left": left.get("valid"),
            "right": right.get("valid"),
            "severity": "blocker",
        })
        return report
    compare_fields = (
        "checksum_status",
        "manifest_status",
        "helper_log_status",
        "problem_count",
        "blocker_count",
        "warning_count",
        "install_locked",
        "install_execution_enabled",
        "helper_launch_from_gui_enabled",
        "non_dry_run_enabled",
        "real_install_attempted",
    )
    left_summary = left.get("summary", {})
    right_summary = right.get("summary", {})
    for field in compare_fields:
        lv = left_summary.get(field)
        rv = right_summary.get(field)
        if lv != rv:
            severity = "info"
            if field in {"install_execution_enabled", "helper_launch_from_gui_enabled", "non_dry_run_enabled", "real_install_attempted"} and (lv or rv):
                severity = "blocker"
            elif field in {"checksum_status", "manifest_status", "helper_log_status", "blocker_count"}:
                severity = "warning"
            report["differences"].append({"field": field, "left": lv, "right": rv, "severity": severity})
            report["changed_fields"].append(field)
    report["difference_count"] = len(report["differences"])
    report["blocker_count"] = len([d for d in report["differences"] if d.get("severity") == "blocker"])
    report["warning_count"] = len([d for d in report["differences"] if d.get("severity") == "warning"])
    report["headline"] = "Diagnostics bundles match on tracked staged-update states."
    if report["blocker_count"]:
        report["headline"] = "Diagnostics comparison found unsafe lock-state differences."
    elif report["warning_count"]:
        report["headline"] = "Diagnostics comparison found staged-update state changes to review."
    elif report["difference_count"]:
        report["headline"] = "Diagnostics comparison found informational changes."
    return report


STAGED_DIAGNOSTICS_COMPARISON_REVIEW_VERSION = "phase62-diagnostics-comparison-review-v1"


def build_diagnostics_comparison_review(comparison: dict[str, Any]) -> dict[str, Any]:
    """Build a GUI/report friendly read-only summary for diagnostics comparisons.

    This intentionally does not import executable payloads, launch helpers, or change
    updater state. It only turns the Phase 61 comparison report into clearer text
    groups for user review.
    """
    differences = comparison.get("differences", []) if isinstance(comparison, dict) else []
    blockers = [d for d in differences if d.get("severity") == "blocker"]
    warnings = [d for d in differences if d.get("severity") == "warning"]
    infos = [d for d in differences if d.get("severity") == "info"]
    valid = bool(comparison.get("valid")) if isinstance(comparison, dict) else False
    if not valid:
        severity = "blocker"
        headline = "Diagnostics comparison cannot be trusted until both bundles import safely."
    elif blockers:
        severity = "blocker"
        headline = "Diagnostics comparison found unsafe lock-state differences."
    elif warnings:
        severity = "warning"
        headline = "Diagnostics comparison found staged-update changes to review."
    elif infos:
        severity = "info"
        headline = "Diagnostics comparison found only informational changes."
    else:
        severity = "ok"
        headline = "Diagnostics bundles match on tracked staged-update states."

    field_labels = {
        "checksum_status": "Checksum status",
        "manifest_status": "Manifest status",
        "helper_log_status": "Helper dry-run log status",
        "problem_count": "Problem count",
        "blocker_count": "Blocker count",
        "warning_count": "Warning count",
        "install_locked": "Install lock",
        "install_execution_enabled": "Install execution flag",
        "helper_launch_from_gui_enabled": "GUI helper launch flag",
        "non_dry_run_enabled": "Non-dry-run flag",
        "real_install_attempted": "Real install attempted flag",
        "bundle_validity": "Bundle validity",
    }
    rows = []
    for d in differences:
        field = d.get("field")
        rows.append({
            "field": field,
            "label": field_labels.get(str(field), str(field)),
            "before": d.get("left"),
            "after": d.get("right"),
            "severity": d.get("severity", "info"),
            "review_note": _diagnostics_comparison_difference_note(str(field), d.get("severity", "info")),
        })
    next_steps = []
    if not valid:
        next_steps.append("Re-export diagnostics from both staged update reviews and retry the comparison.")
    if blockers:
        next_steps.append("Do not proceed with any installer work until unsafe lock-state differences are explained and fixed.")
    if warnings:
        next_steps.append("Review checksum, manifest, helper dry-run, and blocker-count changes before trusting the newer staged update.")
    if not differences and valid:
        next_steps.append("No tracked differences were found; keep install execution locked until a future unlock-gate phase explicitly changes it.")
    return {
        "review_only": True,
        "version": STAGED_DIAGNOSTICS_COMPARISON_REVIEW_VERSION,
        "valid": valid,
        "severity": severity,
        "headline": headline,
        "difference_count": len(differences),
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "info_count": len(infos),
        "rows": rows,
        "next_steps": next_steps,
        "install_execution_enabled": False,
        "helper_launch_from_gui_enabled": False,
        "non_dry_run_enabled": False,
        "real_install_attempted": False,
    }


def _diagnostics_comparison_difference_note(field: str, severity: str) -> str:
    if field == "checksum_status":
        return "Checksum state changed; verify the staged executable and checksum source before trusting the newer bundle."
    if field == "manifest_status":
        return "Manifest state changed; inspect release-manifest.json parsing and required asset coverage."
    if field == "helper_log_status":
        return "Helper dry-run log state changed; regenerate or inspect the helper dry-run log before proceeding."
    if field in {"install_execution_enabled", "helper_launch_from_gui_enabled", "non_dry_run_enabled", "real_install_attempted"}:
        return "Unsafe updater execution flag changed; this must remain false unless a future unlock-gate phase authorizes it."
    if field == "install_locked":
        return "Install lock state changed; verify this was intentional and gate-approved."
    if field in {"problem_count", "blocker_count", "warning_count"}:
        return "Problem counts changed; compare resolution guidance to understand whether the newer staged update is safer."
    if field == "bundle_validity":
        return "One or both bundles failed safe import validation."
    return "Review this informational difference before relying on the newer staged update diagnostics."



STAGED_DIAGNOSTICS_COMPARISON_EXPORT_VERSION = "phase65-diagnostics-comparison-export-v1"

def export_diagnostics_comparison_report_bundle(
    left_bundle: Path | str,
    right_bundle: Path | str,
    output_zip: Path | str,
) -> dict[str, Any]:
    """Export a safe support/debug bundle for a diagnostics comparison.

    The export is read-only and intentionally excludes executable payloads. It
    contains the comparison review JSON, the lower-level comparison report,
    compact imported summaries for both source bundles, and a README.
    """
    output_zip = Path(output_zip)
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    left_import = import_staged_update_diagnostics_bundle(left_bundle)
    right_import = import_staged_update_diagnostics_bundle(right_bundle)
    comparison = compare_staged_update_diagnostics_bundles(left_bundle, right_bundle)
    review = build_diagnostics_comparison_review(comparison)

    export = {
        "version": STAGED_DIAGNOSTICS_COMPARISON_EXPORT_VERSION,
        "review_only": True,
        "safe_bundle": True,
        "executable_payloads_excluded": True,
        "source_bundles": {
            "before": {"path": str(left_bundle), "valid": left_import.get("valid"), "errors": left_import.get("errors", [])},
            "after": {"path": str(right_bundle), "valid": right_import.get("valid"), "errors": right_import.get("errors", [])},
        },
        "comparison_review": review,
        "comparison": comparison,
        "source_summaries": {
            "before": left_import.get("summary", {}),
            "after": right_import.get("summary", {}),
        },
        "install_execution_enabled": False,
        "helper_launch_from_gui_enabled": False,
        "non_dry_run_enabled": False,
        "real_install_attempted": False,
    }
    readme = "\n".join([
        "Deimos staged-update diagnostics comparison report",
        "",
        "This bundle is safe to share for support/debug review.",
        "It intentionally excludes Deimos.exe, updater helper executables, and any executable payload.",
        "The contents are read-only comparison metadata generated from two diagnostics bundles.",
        "",
        "Files:",
        "- comparison-review.json: user-facing before/after review object",
        "- comparison-report.json: lower-level tracked-field difference report",
        "- source-summaries.json: compact imported staged-update summaries",
        "",
        "Safety state:",
        "- install execution: disabled",
        "- GUI helper launch: disabled",
        "- non-dry-run updater behavior: disabled",
        "- real install attempted: false",
    ])
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.txt", readme)
        zf.writestr("comparison-review.json", json.dumps(review, indent=2, sort_keys=True))
        zf.writestr("comparison-report.json", json.dumps(comparison, indent=2, sort_keys=True))
        zf.writestr("source-summaries.json", json.dumps(export["source_summaries"], indent=2, sort_keys=True))
        zf.writestr("export-metadata.json", json.dumps({k: v for k, v in export.items() if k not in {"comparison_review", "comparison", "source_summaries"}}, indent=2, sort_keys=True))
    export["output_zip"] = str(output_zip)
    export["files"] = ["README.txt", "comparison-review.json", "comparison-report.json", "source-summaries.json", "export-metadata.json"]
    return export


# PHASE66_DIAGNOSTICS_COMPARISON_EXPORT_GUI_POLISH
STAGED_DIAGNOSTICS_COMPARISON_EXPORT_GUI_VERSION = "phase66-diagnostics-comparison-export-gui-v1"


def diagnostics_comparison_export_default_filename(review: dict[str, Any] | None = None) -> str:
    """Return a safe default filename for diagnostics comparison exports.

    The filename is stable, filesystem-safe, and based only on the read-only
    review summary. It never embeds source bundle paths or executable names.
    """
    severity = "unknown"
    differences = 0
    if isinstance(review, dict):
        severity = str(review.get("severity") or "unknown").strip().lower() or "unknown"
        try:
            differences = int(review.get("difference_count") or 0)
        except (TypeError, ValueError):
            differences = 0
    severity = re.sub(r"[^a-z0-9_-]+", "-", severity)[:24] or "unknown"
    return f"deimos-diagnostics-comparison-{severity}-{differences}-changes.zip"


def build_diagnostics_comparison_export_gui_summary(
    review: dict[str, Any] | None,
    export: dict[str, Any] | None = None,
    output_zip: Path | str | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    """Build GUI-facing wording for diagnostics comparison export results.

    This is display/report metadata only. It does not read executable payloads,
    launch updater helpers, install updates, replace Deimos.exe, or relaunch the
    application.
    """
    review = review if isinstance(review, dict) else {}
    export = export if isinstance(export, dict) else {}
    files = list(export.get("files") or [])
    safe_bundle = bool(export.get("safe_bundle")) if export else False
    severity = str(review.get("severity") or "unknown")
    difference_count = int(review.get("difference_count") or 0)
    blocker_count = int(review.get("blocker_count") or 0)
    warning_count = int(review.get("warning_count") or 0)
    filename = diagnostics_comparison_export_default_filename(review)
    if error:
        status = "failed"
        headline = "Diagnostics comparison export failed."
        message = "No install action was attempted; review the error and retry the export."
        next_steps = [
            "Confirm both source diagnostics bundles still exist.",
            "Re-run the comparison and export again.",
            "Share the error text rather than any executable payload.",
        ]
    elif safe_bundle:
        status = "saved"
        headline = "Diagnostics comparison report bundle saved."
        message = "The exported bundle is safe to share for support/debug review and excludes executable payloads."
        next_steps = [
            "Share the exported ZIP with support/debug reviewers if needed.",
            "Keep the original staged update bundles unchanged for repeatable review.",
            "Do not treat diagnostics export as permission to install an update.",
        ]
    else:
        status = "blocked"
        headline = "Diagnostics comparison export was blocked."
        message = "The export did not prove the safe read-only bundle contract."
        next_steps = [
            "Inspect the comparison export contract report.",
            "Re-export diagnostics from the staged update review.",
            "Do not share a bundle that contains executable payloads.",
        ]
    return {
        "version": STAGED_DIAGNOSTICS_COMPARISON_EXPORT_GUI_VERSION,
        "review_only": True,
        "status": status,
        "headline": headline,
        "message": message,
        "default_filename": filename,
        "output_zip": str(output_zip or export.get("output_zip") or ""),
        "severity": severity,
        "difference_count": difference_count,
        "blocker_count": blocker_count,
        "warning_count": warning_count,
        "files": files,
        "safe_bundle": safe_bundle,
        "executable_payloads_excluded": bool(export.get("executable_payloads_excluded")) if export else False,
        "next_steps": next_steps,
        "error": error,
        "install_execution_enabled": False,
        "helper_launch_from_gui_enabled": False,
        "non_dry_run_enabled": False,
        "real_install_attempted": False,
    }


def inspect_diagnostics_comparison_report_bundle(bundle: Path | str) -> dict[str, Any]:
    """Read a Phase 65 comparison export bundle and reject executable payloads."""
    bundle = Path(bundle)
    unsafe_suffixes = {".exe", ".dll", ".bat", ".cmd", ".ps1", ".msi"}
    required = {"README.txt", "comparison-review.json", "comparison-report.json", "source-summaries.json", "export-metadata.json"}
    result: dict[str, Any] = {
        "review_only": True,
        "path": str(bundle),
        "valid": False,
        "safe_bundle": False,
        "errors": [],
        "files": [],
        "install_execution_enabled": False,
        "helper_launch_from_gui_enabled": False,
        "non_dry_run_enabled": False,
        "real_install_attempted": False,
    }
    try:
        with zipfile.ZipFile(bundle) as zf:
            names = zf.namelist()
            result["files"] = names
            unsafe = [n for n in names if Path(n).suffix.lower() in unsafe_suffixes or Path(n).name in {"Deimos.exe", "deimos-updater-helper.exe"}]
            if unsafe:
                result["errors"].append(f"executable payloads are not allowed in comparison exports: {unsafe}")
                return result
            missing = sorted(required.difference(names))
            if missing:
                result["errors"].append(f"missing required comparison export files: {missing}")
                return result
            metadata = json.loads(zf.read("export-metadata.json").decode("utf-8"))
            review = json.loads(zf.read("comparison-review.json").decode("utf-8"))
            result["metadata"] = metadata
            result["review"] = review
    except Exception as exc:
        result["errors"].append(str(exc))
        return result
    result["safe_bundle"] = bool(result.get("metadata", {}).get("safe_bundle") and result.get("metadata", {}).get("executable_payloads_excluded"))
    result["valid"] = result["safe_bundle"] and not result["errors"]
    return result

def compare_staged_update_diagnostics_bundles_for_review(left_bundle: Path | str, right_bundle: Path | str) -> dict[str, Any]:
    """Compare two bundles and return a GUI/report friendly read-only review object."""
    comparison = compare_staged_update_diagnostics_bundles(left_bundle, right_bundle)
    review = build_diagnostics_comparison_review(comparison)
    review["comparison"] = comparison
    return review

# PHASE67_DIAGNOSTICS_COMPARISON_EXPORTED_REPORT_IMPORT_REVIEW
STAGED_DIAGNOSTICS_COMPARISON_REPORT_IMPORT_REVIEW_VERSION = "phase67-diagnostics-comparison-report-import-review-v1"


def build_diagnostics_comparison_report_import_review(bundle: Path | str) -> dict[str, Any]:
    """Import and summarize a safe diagnostics-comparison report export bundle.

    This is read-only support/debug metadata review. The underlying inspector
    rejects executable payloads and this function never launches helpers,
    stages updates, installs updates, replaces Deimos.exe, or relaunches Deimos.
    """
    inspection = inspect_diagnostics_comparison_report_bundle(bundle)
    review = inspection.get("review") if isinstance(inspection.get("review"), dict) else {}
    metadata = inspection.get("metadata") if isinstance(inspection.get("metadata"), dict) else {}
    valid = bool(inspection.get("valid"))
    safe_bundle = bool(inspection.get("safe_bundle"))
    errors = list(inspection.get("errors") or [])
    severity = str(review.get("severity") or ("blocker" if errors else "unknown"))
    try:
        difference_count = int(review.get("difference_count") or 0)
    except (TypeError, ValueError):
        difference_count = 0
    try:
        blocker_count = int(review.get("blocker_count") or 0)
    except (TypeError, ValueError):
        blocker_count = 0
    try:
        warning_count = int(review.get("warning_count") or 0)
    except (TypeError, ValueError):
        warning_count = 0

    if valid:
        headline = "Diagnostics comparison report is safe to review."
        status = "valid"
        next_steps = [
            "Review the comparison headline, severity, and changed rows.",
            "Share the exported comparison report with support/debug reviewers if needed.",
            "Do not treat a diagnostics report as permission to install an update.",
        ]
    elif errors:
        headline = "Diagnostics comparison report import was blocked."
        status = "blocked"
        next_steps = [
            "Re-export the comparison report from Deimos using the safe export flow.",
            "Do not share or import bundles that contain executable payloads.",
            "Share the import error text instead of any staged executable files.",
        ]
    else:
        headline = "Diagnostics comparison report is incomplete."
        status = "incomplete"
        next_steps = [
            "Confirm the ZIP contains the required comparison report files.",
            "Re-run diagnostics comparison export if the bundle is missing metadata.",
            "Keep install behavior locked while reviewing diagnostics only.",
        ]

    return {
        "version": STAGED_DIAGNOSTICS_COMPARISON_REPORT_IMPORT_REVIEW_VERSION,
        "review_only": True,
        "path": str(bundle),
        "status": status,
        "valid": valid,
        "safe_bundle": safe_bundle,
        "headline": headline,
        "severity": severity,
        "difference_count": difference_count,
        "blocker_count": blocker_count,
        "warning_count": warning_count,
        "errors": errors,
        "files": list(inspection.get("files") or []),
        "comparison_headline": review.get("headline") or "",
        "comparison_rows": list(review.get("rows") or []),
        "comparison_next_steps": list(review.get("next_steps") or []),
        "export_metadata_version": metadata.get("version"),
        "executable_payloads_excluded": bool(metadata.get("executable_payloads_excluded")),
        "next_steps": next_steps,
        "install_execution_enabled": False,
        "helper_launch_from_gui_enabled": False,
        "non_dry_run_enabled": False,
        "real_install_attempted": False,
    }

# PHASE68_DIAGNOSTICS_REPORT_IMPORT_GUI_POLISH
STAGED_DIAGNOSTICS_COMPARISON_REPORT_IMPORT_GUI_VERSION = "phase68-diagnostics-report-import-gui-polish-v1"


def build_diagnostics_comparison_report_import_gui_summary(review: dict[str, Any] | None, error: str | None = None) -> dict[str, Any]:
    """Build GUI-safe text metadata for imported comparison report bundles.

    This summary is read-only. It never imports executable payloads, launches the
    updater helper, installs updates, replaces Deimos.exe, or relaunches Deimos.
    """
    review = review if isinstance(review, dict) else {}
    errors = list(review.get("errors") or [])
    if error:
        errors.append(str(error))
    status = str(review.get("status") or ("blocked" if errors else "unknown"))
    valid = bool(review.get("valid"))
    safe_bundle = bool(review.get("safe_bundle"))
    blocked = bool(errors) or status == "blocked" or not valid or not safe_bundle
    severity = str(review.get("severity") or ("blocker" if blocked else "ok"))

    if valid and safe_bundle:
        headline = "Diagnostics comparison report is safe to review."
        message = "The imported report is read-only and contains no executable payloads."
    elif errors:
        headline = "Diagnostics comparison report import was blocked."
        message = "The bundle is unsafe, malformed, or missing required support/debug report files."
    else:
        headline = "Diagnostics comparison report import needs attention."
        message = "The bundle could not be confirmed as a safe exported comparison report."

    return {
        "version": STAGED_DIAGNOSTICS_COMPARISON_REPORT_IMPORT_GUI_VERSION,
        "review_only": True,
        "status": status,
        "valid": valid,
        "safe_bundle": safe_bundle,
        "severity": severity,
        "headline": headline,
        "message": message,
        "path": review.get("path") or "",
        "comparison_headline": review.get("comparison_headline") or "",
        "difference_count": int(review.get("difference_count") or 0),
        "blocker_count": int(review.get("blocker_count") or 0),
        "warning_count": int(review.get("warning_count") or 0),
        "errors": errors,
        "files": list(review.get("files") or []),
        "next_steps": list(review.get("next_steps") or []),
        "executable_payloads_excluded": bool(review.get("executable_payloads_excluded")),
        "diagnostics_report_import_read_only": True,
        "executable_payload_import": False,
        "install_execution_enabled": False,
        "helper_launch_from_gui_enabled": False,
        "non_dry_run_enabled": False,
        "real_install_attempted": False,
    }

