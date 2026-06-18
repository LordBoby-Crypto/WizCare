# Phase 51 - Final Update-Install Implementation Design

Phase 51 documents the future real updater install path without enabling it.

## Status

- Real install execution remains locked.
- GUI helper launch remains locked.
- Automatic install remains locked.
- The helper scaffold remains dry-run only unless a future phase explicitly unlocks the gate.

## Required future install sequence

1. Verify staged release files and checksums.
2. Show staged file review and release manifest review.
3. Show install design review.
4. Build a helper manifest with absolute validated paths.
5. Require explicit final user confirmation.
6. Launch an external helper only after the user confirms.
7. Exit Deimos cleanly before helper replaces files.
8. Helper waits for the current process ID to exit.
9. Helper backs up the current executable into a rollback folder.
10. Helper verifies backup before replacement.
11. Helper replaces the executable.
12. Helper verifies the installed executable hash.
13. Helper writes JSONL logs and documented exit codes.
14. Optional relaunch occurs only after verification and only if explicitly requested.

## Forbidden until unlock

- Replacing `Deimos.exe` in the GUI process.
- Launching the helper automatically.
- Installing on startup/background update checks.
- Reporting success before post-install hash verification.
- Removing rollback artifacts before verification.

## Validation

Run:

```bash
python .codex/scripts/deimos_phase51_install_design_readiness.py . .codex/reports/phase51-readiness.json
```
