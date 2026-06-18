# Phase 35: Release upload safety and updater compatibility

Run this before publishing a release, and again after the Windows build creates `dist/Deimos.exe`.

## Pre-build check

```bash
python .codex/scripts/deimos_release_upload_safety.py . .codex/reports/phase35-release-upload-safety.json
```

## Post-build required check

```bash
python .codex/scripts/deimos_checksum_release_artifacts.py . .codex/reports/release-checksum-report.json --write --require-artifact
python .codex/scripts/deimos_release_upload_safety.py . .codex/reports/phase35-release-upload-safety-postbuild.json --require-artifact
```

## Stable release asset contract

GitHub Releases must keep these raw asset names stable for future updater logic:

- `Deimos.exe`
- `Deimos.exe.sha256`
- `release-manifest.json`

The versioned ZIP may change by version, but the raw updater-facing assets must not be renamed.
