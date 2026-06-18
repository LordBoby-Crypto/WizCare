# Diagnostics Comparison Export GUI Polish

Use this workflow when modifying the diagnostics comparison export/save dialog.

1. Keep the export read-only.
2. Use `diagnostics_comparison_export_default_filename()` for default filenames.
3. Use `build_diagnostics_comparison_export_gui_summary()` for success/failure wording.
4. Verify exported bundles exclude executable payloads.
5. Run the Phase 66 readiness checker before packaging.

```bash
python .codex/scripts/deimos_diagnostics_comparison_export_gui_contract.py
python .codex/scripts/deimos_diagnostics_comparison_export_gui_smoke.py
python .codex/scripts/deimos_phase66_diagnostics_comparison_export_gui_readiness.py
```
