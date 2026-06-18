# Phase 48 - Helper Manifest Post-Build Validation

Phase 48 makes `release-manifest.json` helper-aware in strict post-build mode.

## Rules

- Publishing workflows must generate `dist/Deimos.exe`, `dist/Deimos.exe.sha256`, and `dist/release-manifest.json`.
- Publishing workflows must also build `libs/updater_helper/dist/deimos-updater-helper.exe` and `libs/updater_helper/dist/deimos-updater-helper.exe.sha256`.
- `release-manifest.json` must include both primary and helper artifact entries after a real build.
- The helper remains locked: no GUI launch, no executable replacement, no relaunch, and no non-dry-run install behavior.
- Local pre-build checks may warn instead of fail when build artifacts are absent.

## Required strict post-build command

```bash
python .codex/scripts/deimos_phase48_manifest_postbuild_readiness.py . .codex/reports/phase48-manifest-postbuild-readiness.json --strict-postbuild
```
