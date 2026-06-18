# Updater Install Unlock Gate

Use this workflow before any Codex task tries to add updater install behavior.

1. Run:

```bash
python .codex/scripts/deimos_phase50_install_unlock_readiness.py . .codex/reports/phase50-install-unlock-readiness.json
```

2. Confirm the report says `install_locked=true` and `install_unlocked=false`.
3. Treat any attempt to launch the helper, replace `Deimos.exe`, or relaunch Deimos as blocked unless the user explicitly starts a future implementation phase.
4. Preserve the review-first staged update flow.
