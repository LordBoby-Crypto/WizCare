# Phase 65 - Diagnostics Comparison Export/Share Polish

Phase 65 adds a safe export/share path for diagnostics comparison results.

## Purpose

When two staged-update diagnostics bundles are compared, the result can now be exported as a support/debug ZIP that contains only read-only metadata.

## Export contents

- `README.txt`
- `comparison-review.json`
- `comparison-report.json`
- `source-summaries.json`
- `export-metadata.json`

## Explicit exclusions

The export bundle must not contain executable payloads, including:

- `Deimos.exe`
- `deimos-updater-helper.exe`
- `.exe`, `.dll`, `.msi`, `.bat`, `.cmd`, or `.ps1` payloads

## Safety state

Phase 65 remains review-only:

- no helper launch
- no executable import
- no update install
- no relaunch
- no non-dry-run updater path

## Primary APIs

- `export_diagnostics_comparison_report_bundle(before_zip, after_zip, output_zip)`
- `inspect_diagnostics_comparison_report_bundle(bundle)`

## Validation

Run:

```bash
python .codex/scripts/deimos_phase65_diagnostics_comparison_export_readiness.py
```
