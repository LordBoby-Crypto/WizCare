# Phase 36 update-system scaffold

Phase 36 adds `src/update_system.py` as a conservative, review-first update helper. It is intentionally not wired into GUI startup and does not self-install. Its purpose is to make future updater implementation safe by standardizing release asset names, checksum verification, and staging behavior.

## Stable release contract

- executable: `Deimos.exe`
- checksum: `Deimos.exe.sha256`
- manifest: `release-manifest.json`
- checksum format: `<64-hex-sha256>  Deimos.exe`

## Design status

- update lookup: scaffolded
- release asset validation: scaffolded
- staged download: scaffolded
- checksum verification: scaffolded
- install/replace/relaunch: locked pending future review
