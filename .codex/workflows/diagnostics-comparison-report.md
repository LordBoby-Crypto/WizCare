# Diagnostics Comparison Report Workflow

1. Export staged-update diagnostics from two attempts.
2. Import each bundle with `deimos_staged_update_diagnostics_import.py`.
3. Compare bundles with `deimos_staged_update_diagnostics_comparison.py`.
4. Review changed fields, especially checksum, manifest, helper dry-run log, and lock-state fields.
5. Treat any executable payload or unlocked install state as a blocker.

This workflow is read-only and does not install updates.
