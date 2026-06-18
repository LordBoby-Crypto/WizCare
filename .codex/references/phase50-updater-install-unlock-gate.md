# Phase 50 - Updater Install Unlock Gate

Phase 50 defines the checklist that must pass before any future phase may implement real executable replacement.

## Locked by default

The updater must remain locked until a later implementation phase deliberately removes the lock after review.

Forbidden in Phase 50:

- Launching `deimos-updater-helper.exe` from the GUI.
- Replacing `Deimos.exe`.
- Relaunching Deimos automatically.
- Silent/background/startup installation.
- Deleting rollback backups during the same transaction.

## Required before unlock

A future install implementation must prove all of these:

1. Real Windows `Deimos.exe` and `deimos-updater-helper.exe` artifacts exist.
2. `release-manifest.json` includes metadata and SHA-256 for both artifacts.
3. Staged update review reports `checksum_status=verified`.
4. Updater helper dry-run succeeds against the staged real artifacts.
5. Rollback directory and install log paths are visible to the user.
6. Final confirmation dialog shows target executable, release tag, hashes, staged file paths, rollback path, and helper log path.
7. The lock removal happens in a separate reviewed phase.

## Commands

```bash
python .codex/scripts/deimos_update_install_unlock_gate.py . .codex/reports/phase50-install-unlock-gate.json
python .codex/scripts/deimos_update_install_unlock_gate_smoke.py . .codex/reports/phase50-install-unlock-gate-smoke.json
python .codex/scripts/deimos_phase50_install_unlock_readiness.py . .codex/reports/phase50-install-unlock-readiness.json
```
