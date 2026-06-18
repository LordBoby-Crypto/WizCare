# Phase 44: Updater Helper Artifact Validation

Use this workflow after the updater helper scaffold is built and before any release packaging or install work.

## Goals
- Validate the expected helper artifact name: `deimos-updater-helper.exe`.
- Validate optional checksum format: `<64-hex-sha256>  deimos-updater-helper.exe`.
- Report helper size and hash after a real Windows build.
- Check whether release manifests include helper artifact fields when manifests exist.
- Keep install execution locked.

## Commands

Pre-build mode:

```bash
python .codex/scripts/deimos_phase44_helper_artifact_readiness.py . .codex/reports/phase44-helper-artifact-readiness.json
```

Post-build strict mode:

```bash
python .codex/scripts/deimos_update_helper_artifact_report.py . .codex/reports/phase44-helper-artifact-report.json --write-checksum --require-artifact
python .codex/scripts/deimos_phase44_helper_artifact_readiness.py . .codex/reports/phase44-helper-artifact-readiness-postbuild.json --require-artifact
```

## Guardrail
Do not wire helper launch into the GUI until a later reviewed install phase.
