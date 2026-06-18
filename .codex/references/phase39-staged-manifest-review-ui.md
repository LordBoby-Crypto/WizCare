# Phase 39 - Staged update manifest review UI

Phase 39 adds a review dialog for staged update assets. The dialog must show release tag, checksum status, staged file presence, staged/release sizes, paths, and optional `release-manifest.json` contents.

This phase remains review-only. Do not add executable replacement, relaunch, startup downloads, or automatic installation.

Run:

```bash
python .codex/scripts/deimos_phase39_manifest_review_readiness.py .
```
