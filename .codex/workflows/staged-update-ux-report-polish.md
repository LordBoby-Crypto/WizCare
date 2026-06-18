# Phase 57 staged update UX/report polish

Use this workflow before modifying staged-update dialogs or update-report summaries.

1. Keep staged update UX review-only.
2. Do not add install, helper-launch, executable replacement, relaunch, or automatic update behavior.
3. Use `build_staged_update_ux_summary()` for GUI-facing status summaries.
4. Run:

```bash
python .codex/scripts/deimos_phase57_staged_update_ux_readiness.py .
```

The phase is passing only when checksum, manifest, helper dry-run log, and install-lock states are summarized without unlocking install behavior.
