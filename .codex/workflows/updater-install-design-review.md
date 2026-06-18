# Updater install-design review

Use this workflow before Codex edits any updater install/self-replacement code.

1. Confirm Phase 36-39 staged update flow still compiles.
2. Confirm `src/update_system.py` exposes `build_update_install_design_review`.
3. Confirm install is still disabled: `INSTALL_ENABLED = False`.
4. Run the Phase 40 readiness check.
5. If adding a real install path in the future, require a separate helper executable and a user-approved design review first.

Command:

```bash
python .codex/scripts/deimos_phase40_install_design_readiness.py . .codex/reports/phase40-install-design-readiness.json
```
