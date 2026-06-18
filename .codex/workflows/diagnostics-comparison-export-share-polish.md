# Workflow: Diagnostics Comparison Export/Share Polish

Use this workflow when checking or maintaining the Phase 65 diagnostics comparison export path.

1. Generate or select two staged-update diagnostics ZIP bundles.
2. Compare them through the diagnostics comparison GUI or script path.
3. Export the comparison report bundle.
4. Confirm the export contains only metadata and text/json files.
5. Confirm no executable payload is present.
6. Run the readiness checker:

```bash
python .codex/scripts/deimos_phase65_diagnostics_comparison_export_readiness.py
```

The export/share path is read-only and must never enable installation, helper launch, executable import, or relaunch behavior.
