# Workflow - Diagnostics Comparison Exported-Report Import/Review

Use this workflow when reviewing a diagnostics-comparison export bundle from Deimos.

1. Confirm the input is a comparison report ZIP created by the diagnostics comparison export flow.
2. Run:

   ```bash
   python .codex/scripts/deimos_diagnostics_comparison_report_import.py path/to/comparison-report.zip
   ```

3. Review the returned status, headline, severity, changed-row count, blocker count, warning count, and errors.
4. If the bundle is blocked, re-export using the safe comparison export flow.
5. Do not share or import bundles containing executables or script payloads.
6. Keep install behavior locked. This workflow is support/debug review only.

For full readiness validation, run:

```bash
python .codex/scripts/deimos_phase67_diagnostics_report_import_readiness.py
```
