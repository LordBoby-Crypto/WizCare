# Phase 67 - Diagnostics Comparison Exported-Report Import/Review

Phase 67 adds a safe reader for diagnostics-comparison report bundles exported by the Phase 65/66 flow.

## Scope

The import/review flow is support/debug only. It reads a comparison export ZIP, verifies the expected safe structure, rejects executable payloads, and returns a compact review summary.

Required export files:

- `README.txt`
- `comparison-review.json`
- `comparison-report.json`
- `source-summaries.json`
- `export-metadata.json`

## Safety contract

The import/review flow must remain read-only:

- no executable payload import
- no helper launch
- no install execution
- no non-dry-run behavior
- no real install attempt

Any bundle containing `Deimos.exe`, `deimos-updater-helper.exe`, `.exe`, `.dll`, `.msi`, `.bat`, `.cmd`, or `.ps1` payloads must be rejected.

## Scripts

- `.codex/scripts/deimos_diagnostics_comparison_report_import.py COMPARISON-REPORT.zip`
- `.codex/scripts/deimos_diagnostics_comparison_report_import_contract.py`
- `.codex/scripts/deimos_diagnostics_comparison_report_import_smoke.py`
- `.codex/scripts/deimos_phase67_diagnostics_report_import_readiness.py`

## Acceptance gate

Run:

```bash
python .codex/scripts/deimos_phase67_diagnostics_report_import_readiness.py
```

Expected result: passed with zero blockers, executable import disabled, helper launch disabled, install execution disabled, and real install attempted false.
