# Staged download review flow

Use this workflow when editing the manual update UI or staged-update helpers.

1. Confirm `src/update_system.py` still has only non-installing staging helpers.
2. Confirm `src/gui/update_check.py` exposes staged download only after an update is available and stable assets exist.
3. Confirm locale keys exist in both `locale/en.lang` and `locale/zh.lang`.
4. Run the Phase 38 readiness check.
5. Do not add executable replacement or automatic relaunch behavior in this phase.
