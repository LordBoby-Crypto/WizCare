# Release/version consistency workflow

Use before release packaging, updater work, or version bumps.

1. Inspect `Deimos.py` and `pyproject.toml`.
2. Run `.codex/scripts/deimos_version_consistency_report.py .`.
3. If versions differ, either set `pyproject.toml` to the existing `Deimos.py` `tool_version`, or ask the release owner for the intended new version and update both together.
4. Run `.codex/scripts/deimos_release_readiness_report.py .`.
5. Treat version mismatch and locale-key mismatch as blockers.
