# Phase 56: GUI staged-log detection polish

Use this workflow before changing staged update/helper dry-run review UI.

1. Keep install execution locked. The GUI must not launch `deimos-updater-helper.exe`, replace `Deimos.exe`, relaunch Deimos, or run non-dry-run install logic.
2. Run:

```bash
python .codex/scripts/deimos_phase56_staged_log_detection_readiness.py . .codex/reports/phase56-staged-log-detection-readiness.json
```

3. Confirm staged helper dry-run logs are classified as:
   - `missing`: no `deimos-updater-helper.log`
   - `invalid`: unreadable/non-JSONL log entries
   - `incomplete`: JSONL log exists but lacks required dry-run events
   - `valid`: includes `manifest_loaded`, `checksum_verified`, and `dry_run_complete`
4. If UI text changes, update both `locale/en.lang` and `locale/zh.lang` with matching keys.
