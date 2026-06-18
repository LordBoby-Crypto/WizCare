# Phase 54 - Helper Dry-Run GUI Review

Use this workflow before changing update GUI install behavior. The GUI may review helper dry-run command previews and existing helper logs, but it must not launch the helper or install updates.

Run:

```bash
python .codex/scripts/deimos_phase54_helper_dryrun_gui_readiness.py . .codex/reports/phase54-helper-dryrun-gui-readiness.json
```

Required locks:
- helper launch from GUI remains disabled
- non-dry-run execution remains disabled
- Deimos.exe replacement remains disabled
- relaunch remains disabled
