# Phase 64 Reference - Diagnostics Comparison Menu/Button Wiring

Phase 64 wires the existing diagnostics comparison dialog into the GUI with a dedicated `Compare diagnostics` button.

## User flow

1. Open the tool info/update area.
2. Click `Compare diagnostics`.
3. Select the earlier exported staged-update diagnostics ZIP.
4. Select the later exported staged-update diagnostics ZIP.
5. Review the before/after comparison summary and detailed JSON.

## Implementation notes

- The button is added in `src/gui/tab_hotkeys.py` near the existing `Check for Updates` button.
- The button calls `show_diagnostics_comparison_dialog(ctx)` from `src/gui/update_check.py`.
- The dialog uses the Phase 62/63 comparison review path.
- The operation remains read-only.

## Required locale key

- `tooltip_compare_diagnostics_bundles`

## Locked behavior

- `install_execution_enabled: false`
- `helper_launch_from_gui_enabled: false`
- `non_dry_run_enabled: false`
- `real_install_attempted: false`
- `executable_payload_import: false`
