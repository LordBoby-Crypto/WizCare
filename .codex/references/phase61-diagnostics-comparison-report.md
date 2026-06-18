# Phase 61 - Diagnostics Comparison Report

Phase 61 adds read-only comparison for two exported staged-update diagnostics bundles.

## Guarantees

- Diagnostics bundles are imported without executing anything.
- Bundles containing executable payloads are rejected.
- Comparison tracks checksum, manifest, helper dry-run log, problem counts, warning/blocker counts, and install-lock state.
- Install execution, helper launch, non-dry-run behavior, and real replacement remain disabled.

## Commands

```bash
python .codex/scripts/deimos_staged_update_diagnostics_import.py bundle.zip report.json
python .codex/scripts/deimos_staged_update_diagnostics_comparison.py before.zip after.zip comparison.json
python .codex/scripts/deimos_phase61_diagnostics_comparison_readiness.py
```
