# Phase 64 - Diagnostics Comparison Menu/Button Wiring

Phase 64 exposes the Phase 63 read-only diagnostics comparison action from the GUI tool-info area near the update controls.

## Safety contract

The button only opens two exported diagnostics ZIP bundles and displays a read-only comparison review. It must not:

- import executable payloads
- launch the updater helper
- stage or install updates
- replace `Deimos.exe`
- relaunch Deimos
- enable non-dry-run install behavior

The underlying diagnostics importer rejects executable payloads, and the GUI action remains review-only.

## Validation

Run:

```bash
python .codex/scripts/deimos_phase64_diagnostics_comparison_gui_wiring_readiness.py
```

Expected result: `passed: true` and zero blockers.
