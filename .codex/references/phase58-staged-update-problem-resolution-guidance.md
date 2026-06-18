# Phase 58: Staged Update Problem-Resolution Guidance

Adds display/report guidance for staged update problem states.

Codex must keep install execution locked. Use these checks to explain what to fix when staged update review reports missing assets, checksum mismatch, invalid manifest, missing or incomplete helper dry-run logs, or install-lock status.

Run:

```bash
python .codex/scripts/deimos_phase58_resolution_readiness.py .codex/reports/phase58-resolution-readiness.json
```

This phase is review-only and must not add helper launch, executable replacement, relaunch behavior, or automatic installation.
