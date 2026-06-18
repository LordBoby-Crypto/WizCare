# Phase 47: Helper Artifact Post-Build Enforcement

Use this workflow after changing updater-helper build, release packaging, or GitHub Actions artifact upload logic.

## Required checks

```bash
python .codex/scripts/deimos_helper_postbuild_enforcement.py . .codex/reports/phase47-helper-postbuild-enforcement.json
python .codex/scripts/deimos_phase47_helper_postbuild_readiness.py . .codex/reports/phase47-helper-postbuild-readiness.json
```

## Policy

- `build.yml`, `develop.yml`, and `release.yml` must build the helper executable and must fail if the helper executable or checksum is missing after the helper build step.
- Publishing/package workflows must not use `-ErrorAction SilentlyContinue` for helper artifacts.
- `ci.yml` may remain preflight-oriented and does not need to upload helper artifacts.
- Installation remains locked: no workflow or GUI path may launch the helper for real installation.

## Stable helper artifacts

```text
deimos-updater-helper.exe
deimos-updater-helper.exe.sha256
```
