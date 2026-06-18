# Phase 59: Staged Update Diagnostics Export

Phase 59 adds a single diagnostics export artifact for staged update issues. The bundle includes JSON state for staged asset review, checksum status, manifest parse status, helper dry-run log status, problem-resolution guidance, and install-lock state.

Safety rules:

- Exclude `Deimos.exe` and executable payloads from the diagnostics ZIP.
- Include only review artifacts such as `Deimos.exe.sha256`, `release-manifest.json`, `deimos-helper-manifest.json`, and `deimos-updater-helper.log` when present.
- Preserve `install_locked=true`, `helper_launch_from_gui_enabled=false`, `install_execution_enabled=false`, and `non_dry_run_enabled=false`.
