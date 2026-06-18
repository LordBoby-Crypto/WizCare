# Phase 59: Staged Update Diagnostics Export

Use this workflow when a staged update review has problems or warnings and the user needs one safe diagnostics bundle.

1. Stage update files through the GUI or CLI.
2. Generate a helper dry-run log with `.codex/scripts/deimos_helper_dryrun_log_generator.py` if needed.
3. Use the GUI **Export Diagnostics Bundle** action from the staged update review dialog, or call `export_staged_update_diagnostics_bundle(...)`.
4. Confirm the diagnostics ZIP does not include `Deimos.exe` or any executable payload.
5. Run `python .codex/scripts/deimos_phase59_diagnostics_export_readiness.py .`.

Install execution remains locked. This workflow must not launch helpers, replace `Deimos.exe`, relaunch Deimos, or enable non-dry-run installation.
