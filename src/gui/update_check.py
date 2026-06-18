"""Manual update-check GUI integration for the conservative update system.

Phase 40 adds a disabled install-design review after the staged manifest review dialog. Users can inspect staged file
paths, sizes, checksum status, release tag, and optional release-manifest JSON.
This module still does not install, replace, relaunch, or modify Deimos.exe.
"""

from __future__ import annotations

from pathlib import Path
import json
import webbrowser

from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from src.update_system import (
    STABLE_CHECKSUM_ASSET,
    STABLE_EXE_ASSET,
    STABLE_MANIFEST_ASSET,
    ReleaseInfo,
    UpdateCheckResult,
    build_staged_asset_review,
    build_staged_update_ux_summary,
    build_staged_update_problem_resolution_guidance,
    export_staged_update_diagnostics_bundle,
    build_update_install_design_review,
    build_helper_dry_run_review,
    check_for_update,
    compare_staged_update_diagnostics_bundles_for_review,
    export_diagnostics_comparison_report_bundle,
    build_diagnostics_comparison_export_gui_summary,
    diagnostics_comparison_export_default_filename,
    build_diagnostics_comparison_report_import_review,
    build_diagnostics_comparison_report_import_gui_summary,
    stage_release_assets,
)


class _UpdateCheckWorker(QObject):
    finished = pyqtSignal(object)

    def __init__(self, current_version: str, repo: str):
        super().__init__()
        self.current_version = current_version
        self.repo = repo

    def run(self):
        try:
            result = check_for_update(self.current_version, repo=self.repo)
            self.finished.emit((True, result))
        except Exception as exc:  # keep GUI failure-safe
            self.finished.emit((False, str(exc)))


class _StageDownloadWorker(QObject):
    finished = pyqtSignal(object)

    def __init__(self, release: ReleaseInfo, stage_dir: Path):
        super().__init__()
        self.release = release
        self.stage_dir = stage_dir

    def run(self):
        try:
            paths = stage_release_assets(self.release, self.stage_dir)
            self.finished.emit((True, {name: str(path) for name, path in paths.items()}))
        except Exception as exc:  # keep GUI failure-safe
            self.finished.emit((False, str(exc)))


def _tl(ctx, key: str, fallback: str, *args) -> str:
    tl = getattr(ctx, "tl", None)
    text = tl(key) if tl else fallback
    if text == key:
        text = fallback
    try:
        return text.format(*args)
    except Exception:
        return text


def _repo_name(ctx) -> str:
    author = getattr(ctx, "tool_author", "Deimos-Wizard101")
    tool_name = getattr(ctx, "tool_name", "Deimos")
    return f"{author}/{tool_name}-Wizard101"


def _remember_thread(ctx, thread: QThread) -> None:
    threads = getattr(ctx, "_deimos_update_threads", None)
    if threads is None:
        threads = []
        setattr(ctx, "_deimos_update_threads", threads)
    threads.append(thread)

    def _cleanup():
        try:
            threads.remove(thread)
        except ValueError:
            pass

    thread.finished.connect(_cleanup)


def _stable_assets_present(release: ReleaseInfo | None) -> bool:
    if not release:
        return False
    return STABLE_EXE_ASSET in release.assets and STABLE_CHECKSUM_ASSET in release.assets


def _stage_folder_name(release: ReleaseInfo) -> str:
    tag = (release.tag_name or "latest").strip().replace("/", "-").replace("\\", "-")
    return f"deimos-update-{tag}"


def _format_review_text(ctx, review: dict, ux_summary: dict | None = None) -> tuple[str, str]:
    status = review.get("checksum_status") or "unknown"
    tag = review.get("release_tag") or "unknown"
    lines = []
    if ux_summary:
        lines.append(_tl(ctx, "update_staged_ux_headline", "Status: {0}", ux_summary.get("headline") or "unknown"))
        lines.append(_tl(ctx, "update_staged_ux_severity", "Review status: {0}", ux_summary.get("severity") or "unknown"))
        lines.append(_tl(ctx, "update_staged_ux_install_lock", "Install execution remains locked."))
        guidance = ux_summary.get("problem_resolution_guidance") if isinstance(ux_summary, dict) else None
        if guidance:
            lines.append("")
            lines.append(_tl(ctx, "update_resolution_header", "Problem-resolution guidance:"))
            problems = guidance.get("problems") or []
            if problems:
                for problem in problems[:8]:
                    lines.append(f"- [{problem.get('severity')}] {problem.get('title')}")
                    steps = problem.get("next_steps") or []
                    if steps:
                        lines.append("  " + _tl(ctx, "update_resolution_next_steps", "Next steps:") + " " + "; ".join(str(step) for step in steps[:3]))
            else:
                lines.append(_tl(ctx, "update_resolution_no_problems", "No staged update problems were detected."))
        lines.append("")
    lines.extend([
        _tl(ctx, "update_review_release_tag", "Release tag: {0}", tag),
        _tl(ctx, "update_review_checksum_status", "Checksum status: {0}", status),
        _tl(ctx, "update_review_install_locked", "Review only: Deimos.exe was not replaced."),
        "",
        _tl(ctx, "update_review_files_header", "Staged files:"),
    ])
    for asset in review.get("assets") or []:
        name = asset.get("name")
        present = "yes" if asset.get("present") else "no"
        staged_size = asset.get("staged_size")
        release_size = asset.get("release_size")
        size_bits = []
        if staged_size is not None:
            size_bits.append(f"staged={staged_size} bytes")
        if release_size is not None:
            size_bits.append(f"release={release_size} bytes")
        size_text = ", ".join(size_bits) if size_bits else "size unknown"
        path = asset.get("staged_path") or "not staged"
        lines.append(f"- {name}: present={present}; {size_text}; {path}")
    manifest = review.get("manifest")
    details_obj = {"staged_asset_review": review, "ux_summary": ux_summary, "manifest": manifest}
    details = json.dumps(details_obj, indent=2, sort_keys=True) if manifest is not None else _tl(ctx, "update_review_manifest_missing", "release-manifest.json was not staged or could not be read.")
    return "\n".join(lines), details





def _format_helper_dry_run_text(ctx, review: dict) -> tuple[str, str]:
    lines = [
        _tl(ctx, "update_helper_dry_run_title", "Helper Dry-Run Review"),
        _tl(ctx, "update_helper_dry_run_locked", "Review only: the helper was not launched and no install was attempted."),
        _tl(ctx, "update_review_release_tag", "Release tag: {0}", review.get("release_tag") or "unknown"),
        _tl(ctx, "update_review_checksum_status", "Checksum status: {0}", review.get("checksum_status") or "unknown"),
        f"helper={review.get('helper_name')}; log_status={review.get('helper_log_status')}",
        _tl(ctx, "update_helper_dry_run_log_status", "Helper log status: {0}", review.get("helper_log_status") or "unknown"),
        review.get("helper_log_message") or "",
        "",
        _tl(ctx, "update_helper_dry_run_command", "Dry-run command preview:"),
        " ".join(str(part) for part in (review.get("helper_command_preview") or [])),
        "",
        _tl(ctx, "update_helper_dry_run_log_events", "Helper log events:"),
    ]
    events = review.get("helper_log_events") or []
    if events:
        for event in events[:20]:
            lines.append(f"- {event.get('event', event)}")
    else:
        lines.append(_tl(ctx, "update_helper_dry_run_log_missing", "No helper dry-run log was found in the staged folder."))
    missing_events = review.get("helper_log_missing_events") or []
    if missing_events:
        lines.append("")
        lines.append(_tl(ctx, "update_helper_dry_run_missing_events", "Missing dry-run log events:"))
        lines.extend(f"- {event}" for event in missing_events)
    invalid_entries = review.get("helper_log_invalid_entries") or []
    if invalid_entries:
        lines.append("")
        lines.append(_tl(ctx, "update_helper_dry_run_invalid_entries", "Invalid dry-run log entries:"))
        lines.extend(f"- {entry}" for entry in invalid_entries[:5])
    blockers = review.get("manifest_blockers_for_review") or []
    if blockers:
        lines.append("")
        lines.append(_tl(ctx, "update_install_design_blockers", "Install blockers:"))
        lines.extend(f"- {b}" for b in blockers)
    details = json.dumps(review, indent=2, sort_keys=True)
    return "\n".join(lines), details

def show_helper_dry_run_review_dialog(ctx, release: ReleaseInfo, staged_paths: dict[str, str | Path]):
    """Show helper dry-run plan/log details without launching the helper."""
    parent = getattr(ctx, "window", None)
    review = build_helper_dry_run_review(release, staged_paths)
    text, details = _format_helper_dry_run_text(ctx, review)
    box = QMessageBox(parent)
    box.setWindowTitle(_tl(ctx, "update_helper_dry_run_title", "Helper Dry-Run Review"))
    box.setText(_tl(ctx, "update_helper_dry_run_summary", "Review the helper dry-run plan. No helper launch or install action is available."))
    box.setInformativeText(text)
    box.setDetailedText(details)
    box.exec()

def _format_install_design_text(ctx, design: dict) -> tuple[str, str]:
    blockers = design.get("blockers") or []
    lines = [
        _tl(ctx, "update_install_design_title", "Update Install Design Review"),
        _tl(ctx, "update_install_design_locked", "Installation is still disabled. This is a design review only."),
        f"helper_required={design.get('helper_required')}; helper={design.get('helper_name')}",
        f"checksum_verified={design.get('checksum_verified')}; staged_exe_present={design.get('staged_exe_present')}",
        "",
        _tl(ctx, "update_install_design_blockers", "Install blockers:"),
    ]
    if blockers:
        lines.extend(f"- {b}" for b in blockers)
    else:
        lines.append("- none")
    details = json.dumps(design, indent=2, sort_keys=True)
    return "\n".join(lines), details


def show_update_install_design_review_dialog(ctx, release: ReleaseInfo, staged_paths: dict[str, str | Path]):
    """Show the disabled future install design without enabling installation."""
    parent = getattr(ctx, "window", None)
    design = build_update_install_design_review(release, staged_paths)
    text, details = _format_install_design_text(ctx, design)
    box = QMessageBox(parent)
    box.setWindowTitle(_tl(ctx, "update_install_design_title", "Update Install Design Review"))
    box.setText(_tl(ctx, "update_install_design_summary", "Review future install requirements. No install action is available."))
    box.setInformativeText(text)
    box.setDetailedText(details)
    design_button = box.addButton(_tl(ctx, "update_install_design_button", "Review Install Design"), QMessageBox.ButtonRole.ActionRole)
    box.addButton(QMessageBox.StandardButton.Ok)
    box.exec()
    if box.clickedButton() == design_button:
        show_update_install_design_review_dialog(ctx, release, staged_paths)


def export_staged_update_diagnostics_dialog(ctx, release: ReleaseInfo, staged_paths: dict[str, str | Path]):
    """Export a safe diagnostics ZIP for a staged update review.

    The exported ZIP intentionally excludes executable payloads and does not
    install, launch helpers, replace Deimos.exe, or relaunch Deimos.
    """
    parent = getattr(ctx, "window", None)
    default_name = f"deimos-staged-update-diagnostics-{(release.tag_name or 'latest').replace('/', '-')}.zip"
    filename, _ = QFileDialog.getSaveFileName(
        parent,
        _tl(ctx, "update_export_diagnostics", "Export Diagnostics Bundle"),
        str(Path.home() / default_name),
        "Zip Files (*.zip)",
    )
    if not filename:
        return
    try:
        path = export_staged_update_diagnostics_bundle(release, staged_paths, Path(filename))
        box = QMessageBox(parent)
        box.setWindowTitle(_tl(ctx, "update_diagnostics_saved_title", "Diagnostics Bundle Saved"))
        box.setText(_tl(ctx, "update_diagnostics_saved_message", "Diagnostics were exported to:\n{0}", str(path)))
        box.setInformativeText(_tl(ctx, "update_diagnostics_bundle_locked", "The bundle is review-only and excludes executable payloads."))
        box.exec()
    except Exception as exc:
        box = QMessageBox(parent)
        box.setWindowTitle(_tl(ctx, "update_diagnostics_failed_title", "Diagnostics Export Failed"))
        box.setText(_tl(ctx, "update_diagnostics_failed_message", "Could not export staged update diagnostics."))
        box.setInformativeText(str(exc))
        box.exec()


def show_staged_update_review_dialog(ctx, release: ReleaseInfo, staged_paths: dict[str, str | Path]):
    """Show staged file/checksum/manifest details without installing anything."""
    parent = getattr(ctx, "window", None)
    review = build_staged_asset_review(release, staged_paths)
    ux_summary = build_staged_update_ux_summary(release, staged_paths)
    guidance = build_staged_update_problem_resolution_guidance(release, staged_paths)
    ux_summary = {**ux_summary, "problem_resolution_guidance": guidance}
    text, details = _format_review_text(ctx, review, ux_summary)
    box = QMessageBox(parent)
    box.setWindowTitle(_tl(ctx, "update_review_title", "Staged Update Review"))
    box.setText(_tl(ctx, "update_review_summary", "Review staged update files before any future install step."))
    box.setInformativeText(text)
    box.setDetailedText(details)
    helper_button = box.addButton(_tl(ctx, "update_helper_dry_run_button", "Review Helper Dry Run"), QMessageBox.ButtonRole.ActionRole)
    box.addButton(QMessageBox.StandardButton.Ok)
    box.exec()
    if box.clickedButton() == helper_button:
        show_helper_dry_run_review_dialog(ctx, release, staged_paths)


def _show_staging_result(ctx, release: ReleaseInfo, ok: bool, data):
    parent = getattr(ctx, "window", None)
    if ok:
        staged_paths = data if isinstance(data, dict) else {}
        primary = staged_paths.get(STABLE_EXE_ASSET) or next(iter(staged_paths.values()), "")
        folder = str(Path(primary).parent) if primary else ""
        box = QMessageBox(parent)
        box.setWindowTitle(_tl(ctx, "update_staging_success_title", "Update Downloaded"))
        box.setText(_tl(ctx, "update_staging_success_message", "Update assets were downloaded and verified in:\n{0}", folder))
        details = [
            _tl(ctx, "update_staging_locked", "Downloaded files are staged only; Deimos.exe was not replaced."),
            "",
            "Files:",
        ]
        for name in (STABLE_EXE_ASSET, STABLE_CHECKSUM_ASSET, STABLE_MANIFEST_ASSET):
            if name in staged_paths:
                details.append(f"- {name}: {staged_paths[name]}")
        box.setInformativeText("\n".join(details))
        review_button = box.addButton(_tl(ctx, "update_review_staged_files", "Review Staged Files"), QMessageBox.ButtonRole.ActionRole)
        box.addButton(QMessageBox.StandardButton.Ok)
        box.exec()
        if box.clickedButton() == review_button:
            show_staged_update_review_dialog(ctx, release, staged_paths)
    else:
        box = QMessageBox(parent)
        box.setWindowTitle(_tl(ctx, "update_staging_failed_title", "Update Download Failed"))
        box.setText(_tl(ctx, "update_staging_failed_message", "Could not download and verify update assets."))
        box.setInformativeText(str(data))
        box.exec()


def show_staged_download_dialog(ctx, release: ReleaseInfo):
    """Download stable release assets to a user-selected staging folder.

    This is intentionally a review-only flow. It verifies SHA-256 but never
    installs, replaces, or launches executables.
    """
    parent = getattr(ctx, "window", None)
    root = QFileDialog.getExistingDirectory(
        parent,
        _tl(ctx, "update_choose_staging_folder", "Choose Update Staging Folder"),
        str(Path.home()),
    )
    if not root:
        QMessageBox.information(parent, _tl(ctx, "update_staging_cancelled", "Update download cancelled."), _tl(ctx, "update_staging_locked", "Downloaded files are staged only; Deimos.exe was not replaced."))
        return

    stage_dir = Path(root) / _stage_folder_name(release)
    progress = QMessageBox(parent)
    progress.setWindowTitle(_tl(ctx, "update_download_to_staging", "Download to Staging Folder"))
    progress.setText(_tl(ctx, "update_staging_downloading", "Downloading update assets..."))
    progress.setInformativeText(str(stage_dir))
    progress.setStandardButtons(QMessageBox.StandardButton.NoButton)
    progress.show()

    thread = QThread(parent)
    worker = _StageDownloadWorker(release=release, stage_dir=stage_dir)
    worker.moveToThread(thread)
    _remember_thread(ctx, thread)

    def _finished(payload):
        ok, data = payload
        try:
            progress.done(0)
            _show_staging_result(ctx, release, ok, data)
        finally:
            thread.quit()
            worker.deleteLater()

    worker.finished.connect(_finished)
    thread.started.connect(worker.run)
    thread.finished.connect(thread.deleteLater)
    thread.start()


def _show_result_dialog(ctx, result: UpdateCheckResult):
    release = result.release
    warnings = list(result.warnings or [])
    latest = result.latest_version or _tl(ctx, "update_unknown_version", "unknown")

    if result.update_available:
        title = _tl(ctx, "update_available_title", "Update Available")
        message = _tl(ctx, "update_available_message", "Deimos {0} is available. You are running {1}.", latest, result.current_version)
    else:
        title = _tl(ctx, "update_not_available_title", "No Update Available")
        message = _tl(ctx, "update_not_available_message", "You are running the latest known version: {0}.", result.current_version)

    detail_lines = [
        _tl(ctx, "update_asset_contract", "Expected release assets: Deimos.exe, Deimos.exe.sha256, release-manifest.json"),
        _tl(ctx, "update_install_locked", "Automatic installation is disabled in this build."),
        _tl(ctx, "update_staging_locked", "Downloaded files are staged only; Deimos.exe was not replaced."),
    ]
    if warnings:
        detail_lines.append("")
        detail_lines.append(_tl(ctx, "update_warnings_header", "Warnings:"))
        detail_lines.extend(f"- {w}" for w in warnings)

    box = QMessageBox(getattr(ctx, "window", None))
    box.setWindowTitle(title)
    box.setText(message)
    box.setInformativeText("\n".join(detail_lines))
    open_button = None
    stage_button = None
    if release and release.html_url:
        open_button = box.addButton(_tl(ctx, "update_open_release", "Open Release Page"), QMessageBox.ButtonRole.ActionRole)
    if result.update_available and _stable_assets_present(release):
        stage_button = box.addButton(_tl(ctx, "update_download_to_staging", "Download to Staging Folder"), QMessageBox.ButtonRole.ActionRole)
    box.addButton(QMessageBox.StandardButton.Ok)
    box.exec()
    clicked = box.clickedButton()
    if open_button is not None and clicked == open_button:
        webbrowser.open(release.html_url)
    elif stage_button is not None and clicked == stage_button and release is not None:
        show_staged_download_dialog(ctx, release)


def show_update_check_dialog(ctx, button=None):
    """Start a non-installing update check and show the result in a dialog."""
    if button is not None:
        button.setEnabled(False)
        button.setText(_tl(ctx, "update_checking", "Checking..."))

    parent = getattr(ctx, "window", None)
    current_version = str(getattr(ctx, "tool_version", "0.0.0"))
    repo = _repo_name(ctx)

    thread = QThread(parent)
    worker = _UpdateCheckWorker(current_version=current_version, repo=repo)
    worker.moveToThread(thread)
    _remember_thread(ctx, thread)

    def _restore_button():
        if button is not None:
            button.setEnabled(True)
            button.setText(_tl(ctx, "check_for_updates", "Check for Updates"))

    def _finished(payload):
        ok, data = payload
        _restore_button()
        try:
            if ok:
                _show_result_dialog(ctx, data)
            else:
                box = QMessageBox(parent)
                box.setWindowTitle(_tl(ctx, "update_error_title", "Update Check Failed"))
                box.setText(_tl(ctx, "update_error_message", "Could not check for updates."))
                box.setInformativeText(str(data))
                box.exec()
        finally:
            thread.quit()
            worker.deleteLater()

    worker.finished.connect(_finished)
    thread.started.connect(worker.run)
    thread.finished.connect(thread.deleteLater)
    thread.start()


# PHASE63_DIAGNOSTICS_COMPARISON_GUI_ACTION_SCAFFOLD

def _format_diagnostics_comparison_review_text(ctx, review: dict) -> tuple[str, str]:
    """Format a read-only diagnostics bundle comparison for GUI review."""
    lines = [
        _tl(ctx, "update_diagnostics_compare_title", "Compare Diagnostics Bundles"),
        _tl(ctx, "update_diagnostics_compare_locked", "Review only: no executables are imported and no install action is available."),
        _tl(ctx, "update_diagnostics_compare_headline", "Result: {0}", review.get("headline") or "unknown"),
        _tl(ctx, "update_diagnostics_compare_severity", "Severity: {0}", review.get("severity") or "unknown"),
        f"differences={review.get('difference_count', 0)}; blockers={review.get('blocker_count', 0)}; warnings={review.get('warning_count', 0)}",
        "",
    ]
    rows = review.get("rows") or []
    if rows:
        lines.append(_tl(ctx, "update_diagnostics_compare_changes", "Changes:"))
        for row in rows[:30]:
            lines.append(f"- [{row.get('severity')}] {row.get('label')}: {row.get('before')} -> {row.get('after')}")
            note = row.get("review_note")
            if note:
                lines.append(f"  {note}")
    else:
        lines.append(_tl(ctx, "update_diagnostics_compare_no_changes", "No tracked staged-update state changes were found."))
    next_steps = review.get("next_steps") or []
    if next_steps:
        lines.append("")
        lines.append(_tl(ctx, "update_diagnostics_compare_next_steps", "Next steps:"))
        lines.extend(f"- {step}" for step in next_steps[:8])
    details = json.dumps(review, indent=2, sort_keys=True)
    return "\n".join(lines), details


def show_diagnostics_comparison_dialog(ctx):
    """Open two diagnostics ZIPs and show a read-only comparison summary.

    This GUI action scaffold only reads safe diagnostics bundles. The importer
    rejects executable payloads, and this function never launches helpers,
    stages updates, replaces Deimos.exe, relaunches Deimos, or enables install.
    """
    parent = getattr(ctx, "window", None)
    before, _ = QFileDialog.getOpenFileName(
        parent,
        _tl(ctx, "update_diagnostics_compare_choose_before", "Choose Earlier Diagnostics Bundle"),
        str(Path.home()),
        "Zip Files (*.zip)",
    )
    if not before:
        return
    after, _ = QFileDialog.getOpenFileName(
        parent,
        _tl(ctx, "update_diagnostics_compare_choose_after", "Choose Later Diagnostics Bundle"),
        str(Path.home()),
        "Zip Files (*.zip)",
    )
    if not after:
        return
    try:
        review = compare_staged_update_diagnostics_bundles_for_review(before, after)
        text, details = _format_diagnostics_comparison_review_text(ctx, review)
        box = QMessageBox(parent)
        box.setWindowTitle(_tl(ctx, "update_diagnostics_compare_title", "Compare Diagnostics Bundles"))
        box.setText(review.get("headline") or _tl(ctx, "update_diagnostics_compare_summary", "Diagnostics comparison completed."))
        box.setInformativeText(text)
        box.setDetailedText(details)
        box.exec()
        default_name = diagnostics_comparison_export_default_filename(review)
        save_path, _ = QFileDialog.getSaveFileName(
            parent,
            _tl(ctx, "update_diagnostics_compare_export_title", "Export Diagnostics Comparison Report"),
            str(Path.home() / default_name),
            "Zip Files (*.zip)",
        )
        if save_path:
            if not save_path.lower().endswith(".zip"):
                save_path += ".zip"
            export = export_diagnostics_comparison_report_bundle(before, after, save_path)
            summary = build_diagnostics_comparison_export_gui_summary(review, export, save_path)
            saved = QMessageBox(parent)
            saved.setWindowTitle(_tl(ctx, "update_diagnostics_compare_export_saved_title", "Diagnostics Comparison Exported"))
            saved.setText(_tl(ctx, "update_diagnostics_compare_export_saved_message", "Comparison report bundle saved."))
            saved.setInformativeText("\n".join([
                summary.get("headline") or "",
                summary.get("message") or "",
                _tl(ctx, "update_diagnostics_compare_export_path", "Saved to: {0}", summary.get("output_zip") or save_path),
                _tl(ctx, "update_diagnostics_compare_export_safety", "The bundle is read-only and excludes executable payloads."),
            ]))
            saved.setDetailedText(json.dumps(summary, indent=2, sort_keys=True))
            saved.exec()
    except Exception as exc:  # GUI review/export must fail closed and read-only.
        summary = build_diagnostics_comparison_export_gui_summary({}, {}, None, str(exc))
        box = QMessageBox(parent)
        box.setWindowTitle(_tl(ctx, "update_diagnostics_compare_failed_title", "Diagnostics Comparison Failed"))
        box.setText(_tl(ctx, "update_diagnostics_compare_failed_message", "Could not compare diagnostics bundles."))
        box.setInformativeText("\n".join([
            summary.get("headline") or "",
            summary.get("message") or "",
            str(exc),
        ]))
        box.setDetailedText(json.dumps(summary, indent=2, sort_keys=True))
        box.exec()

# PHASE68_DIAGNOSTICS_REPORT_IMPORT_GUI_POLISH

DIAGNOSTICS_REPORT_IMPORT_GUI_WIRING_VERSION = "phase69-diagnostics-report-import-gui-wiring-polish-v1"


def build_diagnostics_report_import_gui_wiring_metadata(ctx=None) -> dict:
    """Return safe GUI wiring metadata for the diagnostics report import action.

    The import action is intentionally presented as a support/debug review tool
    so the menu button does not imply update installation, helper launch, or
    executable import behavior.
    """
    return {
        "version": DIAGNOSTICS_REPORT_IMPORT_GUI_WIRING_VERSION,
        "action_id": "import_diagnostics_comparison_report",
        "label": _tl(ctx, "update_diagnostics_report_import", "Import diagnostics report"),
        "tooltip": _tl(
            ctx,
            "tooltip_import_diagnostics_comparison_report",
            "Import and review a safe exported diagnostics comparison report. Review only; no executables are imported and no install action is available.",
        ),
        "safety_note": _tl(
            ctx,
            "update_diagnostics_report_import_button_safety",
            "Read-only support/debug review; executables and install actions stay blocked.",
        ),
        "review_only": True,
        "diagnostics_report_import_read_only": True,
        "executable_payload_import": False,
        "install_execution_enabled": False,
        "helper_launch_from_gui_enabled": False,
        "non_dry_run_enabled": False,
        "real_install_attempted": False,
    }


def _format_diagnostics_comparison_report_import_text(ctx, review: dict, summary: dict) -> tuple[str, str]:
    """Format a safe imported diagnostics comparison report for GUI review."""
    lines = [
        _tl(ctx, "update_diagnostics_report_import_title", "Review Diagnostics Comparison Report"),
        _tl(ctx, "update_diagnostics_report_import_locked", "Review only: no executables are imported and no install action is available."),
        _tl(ctx, "update_diagnostics_report_import_button_safety", "Read-only support/debug review; executables and install actions stay blocked."),
        _tl(ctx, "update_diagnostics_report_import_status", "Status: {0}", summary.get("status") or "unknown"),
        _tl(ctx, "update_diagnostics_report_import_severity", "Severity: {0}", summary.get("severity") or "unknown"),
        summary.get("headline") or "",
        summary.get("message") or "",
        f"differences={summary.get('difference_count', 0)}; blockers={summary.get('blocker_count', 0)}; warnings={summary.get('warning_count', 0)}",
        "",
    ]
    if summary.get("comparison_headline"):
        lines.append(_tl(ctx, "update_diagnostics_report_import_comparison_headline", "Comparison result: {0}", summary.get("comparison_headline")))
    errors = summary.get("errors") or []
    if errors:
        lines.append(_tl(ctx, "update_diagnostics_report_import_errors", "Import problems:"))
        lines.extend(f"- {err}" for err in errors[:10])
    rows = review.get("comparison_rows") or []
    if rows:
        lines.append("")
        lines.append(_tl(ctx, "update_diagnostics_report_import_changes", "Reported changes:"))
        for row in rows[:25]:
            lines.append(f"- [{row.get('severity')}] {row.get('label')}: {row.get('before')} -> {row.get('after')}")
    next_steps = summary.get("next_steps") or []
    if next_steps:
        lines.append("")
        lines.append(_tl(ctx, "update_diagnostics_report_import_next_steps", "Next steps:"))
        lines.extend(f"- {step}" for step in next_steps[:8])
    details = json.dumps({"review": review, "summary": summary}, indent=2, sort_keys=True)
    return "\n".join(line for line in lines if line is not None), details


def show_diagnostics_comparison_report_import_dialog(ctx):
    """Open and review a safe exported diagnostics comparison report bundle.

    This action only reads safe support/debug report ZIPs. It rejects executable
    payloads through the update_system inspector and never launches helpers,
    stages updates, replaces Deimos.exe, relaunches Deimos, or enables install.
    """
    parent = getattr(ctx, "window", None)
    bundle, _ = QFileDialog.getOpenFileName(
        parent,
        _tl(ctx, "update_diagnostics_report_import_choose", "Choose Diagnostics Comparison Report"),
        str(Path.home()),
        "Zip Files (*.zip)",
    )
    if not bundle:
        return
    try:
        review = build_diagnostics_comparison_report_import_review(bundle)
        summary = build_diagnostics_comparison_report_import_gui_summary(review)
        text, details = _format_diagnostics_comparison_report_import_text(ctx, review, summary)
        box = QMessageBox(parent)
        box.setWindowTitle(_tl(ctx, "update_diagnostics_report_import_title", "Review Diagnostics Comparison Report"))
        if summary.get("valid") and summary.get("safe_bundle"):
            box.setText(_tl(ctx, "update_diagnostics_report_import_safe_title", "Diagnostics report is safe to review."))
        else:
            box.setText(_tl(ctx, "update_diagnostics_report_import_blocked_title", "Diagnostics report import was blocked."))
        box.setInformativeText(text)
        box.setDetailedText(details)
        box.exec()
    except Exception as exc:  # fail closed; read-only import/review only
        summary = build_diagnostics_comparison_report_import_gui_summary({}, str(exc))
        box = QMessageBox(parent)
        box.setWindowTitle(_tl(ctx, "update_diagnostics_report_import_failed_title", "Diagnostics Report Import Failed"))
        box.setText(_tl(ctx, "update_diagnostics_report_import_failed_message", "Could not import diagnostics comparison report."))
        box.setInformativeText("\n".join([summary.get("headline") or "", summary.get("message") or "", str(exc)]))
        box.setDetailedText(json.dumps(summary, indent=2, sort_keys=True))
        box.exec()
