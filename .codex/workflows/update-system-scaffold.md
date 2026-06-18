# Phase 36: Update-system scaffold

Use this workflow before Codex edits or enables Deimos updater behavior.

## Rules

- Treat `src/update_system.py` as review-first infrastructure.
- Do not add automatic replacement of `Deimos.exe` without a separate reviewed helper design.
- Do not add subprocess relaunch behavior in the scaffold.
- Keep stable release asset names aligned with Phase 35:
  - `Deimos.exe`
  - `Deimos.exe.sha256`
  - `release-manifest.json`
- Keep checksum format as `<64-hex-sha256>  Deimos.exe`.

## Required checks

```bash
python .codex/scripts/deimos_update_system_readiness.py . .codex/reports/update-system-readiness.json
```

## Allowed uses

- Check whether a newer GitHub release exists.
- Validate that a release exposes stable updater-facing assets.
- Download release assets to a staging folder.
- Verify `Deimos.exe` using `Deimos.exe.sha256`.

## Not allowed yet

- Replace the running executable.
- Relaunch Deimos.
- Auto-install without explicit user action.
- Change release asset names.
