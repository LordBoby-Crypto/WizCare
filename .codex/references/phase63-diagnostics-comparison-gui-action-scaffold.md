# Phase 63 - Diagnostics Comparison GUI Action Scaffold

Phase 63 adds a GUI-safe action scaffold for comparing two staged-update diagnostics bundles.

## Scope

- Opens an earlier diagnostics ZIP and a later diagnostics ZIP.
- Uses the read-only diagnostics comparison review path from Phase 62.
- Displays headline, severity, changed rows, next steps, and full JSON details.
- Rejects unsafe bundles through the existing diagnostics importer.

## Locked behavior

This phase must not:

- import executable payloads,
- launch updater helpers,
- stage update downloads,
- replace `Deimos.exe`,
- relaunch Deimos,
- enable non-dry-run installation.

The GUI action is a scaffold for future menu/button wiring and remains review-only.
