# Phase 40: updater install-design review

Phase 40 keeps updater installation disabled while documenting the future install path. Codex must not implement executable replacement inside the GUI process. A future install feature requires an external helper process, explicit user confirmation, checksum verification immediately before replacement, rollback backup creation, and post-copy hash verification.

## Hard rules

- Do not replace `Deimos.exe` from the running GUI process.
- Do not silently install updates.
- Do not relaunch Deimos without explicit user confirmation.
- Treat PermissionError/locked-file failures as non-destructive blockers.
- Keep staged files intact on failure.

## Required checks

Run:

```bash
python .codex/scripts/deimos_phase40_install_design_readiness.py . .codex/reports/phase40-install-design-readiness.json
```
