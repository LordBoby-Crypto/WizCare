# Phase 41 - Updater Helper Specification

Phase 41 defines the external helper contract for a future Deimos self-update install path without enabling installation.

## Scope

The GUI process must not replace `Deimos.exe` directly. Any future install flow must delegate executable replacement to a small external helper after Deimos exits.

## Required helper contract

- helper executable name: `deimos-updater-helper.exe`
- manifest: `deimos-helper-manifest.json`
- log: `deimos-updater-helper.log`
- rollback directory: `rollback/`
- required arguments:
  - `--manifest <path>`
  - `--wait-pid <pid>`
  - `--log <path>`
- optional arguments:
  - `--relaunch <path>`
  - `--dry-run`
  - `--timeout-seconds <seconds>`

## Required behavior

1. Validate manifest schema before touching any executable.
2. Wait for Deimos to exit.
3. Verify staged `Deimos.exe` SHA-256.
4. Back up the current executable.
5. Replace only after backup succeeds.
6. Verify post-replacement hash.
7. Roll back if verification fails.
8. Log every step.
9. Relaunch only when explicitly requested.

## Locked behavior

Phase 41 still forbids launching the helper, replacing files, enabling automatic installation, background installs, or silent relaunch.
