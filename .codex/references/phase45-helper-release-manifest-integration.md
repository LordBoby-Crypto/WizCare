# Phase 45 - Helper release-manifest integration

Use this phase before publishing releases that may include the updater helper artifact.

Rules:
- Keep installer execution locked.
- Keep GUI helper launch locked.
- Main required release assets remain `Deimos.exe`, `Deimos.exe.sha256`, and `release-manifest.json`.
- Optional helper assets are `deimos-updater-helper.exe` and `deimos-updater-helper.exe.sha256` until a later phase explicitly requires them.
- `release-manifest.json` may include `updater_contract.updater_helper`, but it must set `launch_from_gui_locked` and `install_execution_locked` to true.

Run:

```bash
python .codex/scripts/deimos_phase45_helper_manifest_readiness.py . .codex/reports/phase45-helper-manifest-readiness.json
```
