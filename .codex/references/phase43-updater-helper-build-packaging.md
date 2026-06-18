# Phase 43 - Updater Helper Build Packaging Scaffold

Phase 43 adds packaging/build scaffolding for the external updater helper without enabling install execution.

## Added pieces

- `libs/updater_helper/deimos_updater_helper.spec`
- `libs/updater_helper/build_helper.py`
- `.codex/scripts/deimos_update_helper_build_contract.py`
- `.codex/scripts/deimos_update_helper_build_smoke.py`
- `.codex/scripts/deimos_phase43_update_helper_build_readiness.py`

## Rules for Codex

- Treat the helper executable as future infrastructure only.
- Keep GUI launch locked.
- Keep executable replacement locked.
- Keep relaunch locked.
- Build checks may verify the spec and dry-run helper behavior only.
- Do not wire the helper into update buttons or startup code.
