# Phase 55 - Staged Helper Dry-Run Log Generation

Phase 55 adds a safe repo-side script for generating a real helper dry-run JSONL log from staged update files. The GUI still does not launch the helper and still cannot install updates.

## Purpose

The Phase 54 GUI review dialog can display helper dry-run log events if a log exists in the staged folder. Phase 55 provides the repo script that creates that log from a staging folder containing:

- `Deimos.exe`
- `Deimos.exe.sha256`

## Command

```bash
python .codex/scripts/deimos_helper_dryrun_log_generator.py . path/to/staging .codex/reports/phase55-helper-dryrun-log.json
```

The script writes:

- `path/to/staging/deimos-helper-manifest.json`
- `path/to/staging/deimos-updater-helper.log`
- a JSON report at the requested output path

## Safety rules

The script invokes `libs/updater_helper/deimos_updater_helper.py` with `--dry-run` only. It never replaces `Deimos.exe`, never relaunches Deimos, never enables automatic installation, and never gives the GUI permission to launch helper execution.

## Required log events

The generated log must include:

- `plan_built`
- `checksum_verified`
- `dry_run_complete`

If any of these are missing, treat the staged update as not ready for review.
