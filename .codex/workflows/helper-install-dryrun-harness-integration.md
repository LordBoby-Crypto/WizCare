# Phase 53: Helper Install Dry-Run Harness Integration

Use this workflow before any future updater install implementation work.

1. Run the aggregate readiness check:
   `python .codex/scripts/deimos_phase53_helper_install_dryrun_readiness.py . .codex/reports/phase53-readiness.json`
2. Confirm the helper runs only with `--dry-run`.
3. Confirm the fake install harness scenarios pass: success, checksum failure, rollback restoration, and exit-code matrix.
4. Do not add GUI helper launch, non-dry-run helper execution, executable replacement, or automatic install behavior in this phase.
