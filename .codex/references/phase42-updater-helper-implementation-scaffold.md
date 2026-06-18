# Phase 42 updater helper implementation scaffold

Phase 42 adds a non-integrated Python helper scaffold under `libs/updater_helper/`. It validates the future helper manifest contract and can run a dry-run checksum verification against staged `Deimos.exe` assets.

## Locked behavior

The helper must not replace files, relaunch Deimos, spawn subprocess installers, or run without `--dry-run`. GUI integration remains review-only.

## Future implementation boundary

A later phase may replace this scaffold with a compiled helper, but it must preserve the argument contract, manifest schema, rollback log model, and exit-code map from Phase 41.
