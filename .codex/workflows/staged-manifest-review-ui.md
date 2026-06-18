# Staged manifest review UI

Use when editing update review behavior after staged downloads.

1. Verify `src/update_system.py` exposes `build_staged_asset_review`.
2. Verify `src/gui/update_check.py` exposes `show_staged_update_review_dialog`.
3. Verify both locale files contain Phase 39 review keys.
4. Run `python .codex/scripts/deimos_phase39_manifest_review_readiness.py .`.
5. Do not add install/relaunch behavior.
