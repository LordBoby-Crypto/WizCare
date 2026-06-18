# Phase 46 - Helper release workflow integration

Phase 46 formally adds helper build/check/upload steps to GitHub Actions while preserving the install lock.

## Stable helper artifacts

- `deimos-updater-helper.exe`
- `deimos-updater-helper.exe.sha256`

## Safe behavior

Allowed:

- Build helper executable in CI/release workflows.
- Generate helper checksum.
- Include helper files in packages/artifacts.
- Add helper metadata to release manifests.

Forbidden:

- Launch helper from GUI/workflows for install.
- Replace `Deimos.exe`.
- Relaunch Deimos.
- Run helper in non-dry-run install mode.
