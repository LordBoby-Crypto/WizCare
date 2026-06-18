# Phase 37 Update-Check GUI Integration

Phase 37 wires the conservative `src/update_system.py` scaffold into the GUI as a manual check only.

Allowed:
- fetch GitHub release metadata from a user-triggered button,
- report current/latest version,
- show missing release-asset warnings,
- open the release page in a browser.

Forbidden in this phase:
- auto-installing updates,
- replacing `Deimos.exe`,
- relaunching Deimos,
- background startup checks,
- downloading executables without explicit future review.

Primary files:
- `src/gui/update_check.py`
- `src/gui/tab_hotkeys.py`
- `src/update_system.py`
- `locale/en.lang`
- `locale/zh.lang`
