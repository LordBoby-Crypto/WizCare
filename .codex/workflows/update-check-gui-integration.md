# Phase 37: Manual update-check GUI integration

Use this workflow before changing update UI behavior.

1. Confirm `src/update_system.py` remains review-first and non-installing.
2. Confirm `src/gui/update_check.py` only checks metadata and opens the release page.
3. Confirm `src/gui/tab_hotkeys.py` exposes a manual `Check for Updates` button.
4. Confirm locale keys are present in both `locale/en.lang` and `locale/zh.lang`.
5. Run:

```bash
python .codex/scripts/deimos_phase37_update_gui_readiness.py . .codex/reports/phase37-update-gui-readiness.json
```

Do not add automatic executable replacement or relaunch behavior in this workflow.
