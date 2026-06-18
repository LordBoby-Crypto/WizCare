# Phase 46 - Helper release workflow integration

Use this workflow when changing GitHub Actions release/build behavior for the updater helper.

## Required checks

```bash
python .codex/scripts/deimos_phase46_helper_workflow_readiness.py . .codex/reports/phase46-helper-workflow-readiness.json
```

## Contract

The workflows may build and publish helper artifacts:

- `libs/updater_helper/dist/deimos-updater-helper.exe`
- `libs/updater_helper/dist/deimos-updater-helper.exe.sha256`

The workflows must not launch the helper, replace `Deimos.exe`, relaunch Deimos, or enable non-dry-run install behavior.
