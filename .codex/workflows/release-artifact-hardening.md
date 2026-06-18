# Release Artifact Hardening

Use this workflow before publishing a Deimos release.

1. Build on Windows with `uv run --group dev pyinstaller --noconfirm --clean Deimos.spec`.
2. Generate checksums and manifest with `python .codex/scripts/deimos_checksum_release_artifacts.py . .codex/reports/release-checksum-report.json --write --require-artifact`.
3. Audit workflows with `python .codex/scripts/deimos_release_workflow_artifact_audit.py . .codex/reports/phase34-workflow-artifact-audit.json`.
4. Confirm release assets include `dist/Deimos.exe`, `dist/Deimos.exe.sha256`, and `dist/release-manifest.json`.
5. Do not publish if checksum or manifest validation has blockers.
