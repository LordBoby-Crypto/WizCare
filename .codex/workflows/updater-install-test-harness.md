# Phase 52 Workflow - Updater Install Test Harness

Use this workflow before any future updater install implementation or helper-launch change.

1. Confirm the current work is simulation-only.
2. Run the aggregate readiness check:

```bash
python .codex/scripts/deimos_phase52_install_harness_readiness.py . .codex/reports/phase52-install-harness-readiness.json
```

3. Inspect the generated harness report and confirm:
   - success scenario verifies a staged fake executable
   - checksum failure stops before replacement
   - replacement failure restores rollback
   - no scenario reports `real_install_attempted: true`
4. Do not enable GUI helper launch or executable replacement in this phase.

Acceptance gate: readiness must pass with zero blockers and install execution must remain disabled.
