# Phase 62 - Diagnostics comparison GUI/report polish

Phase 62 turns the Phase 61 diagnostics comparison report into a user-facing review object.

## Guarantees

- Read-only diagnostics comparison only.
- Executable payload import remains rejected by the underlying diagnostics importer.
- No helper launch.
- No Deimos.exe replacement.
- No non-dry-run updater behavior.

## Review output

The review object includes:

- overall severity: `ok`, `info`, `warning`, or `blocker`
- a human-readable headline
- before/after rows for each changed tracked field
- per-field review notes
- next-step guidance
- locked execution flags

## Use

```bash
python .codex/scripts/deimos_staged_update_diagnostics_comparison_review.py before.zip after.zip .codex/reports/comparison-review.json
python .codex/scripts/deimos_phase62_diagnostics_comparison_review_readiness.py
```
