# Windows Build Command Hardening

Run this workflow before a Windows release build or whenever build/release scripts are edited.

1. Confirm versions are already consistent:
   ```bash
   python .codex/scripts/deimos_version_consistency_report.py . .codex/reports/phase30-version-consistency.json
   ```
2. Run the Windows preflight:
   ```bash
   python .codex/scripts/deimos_windows_build_preflight.py . .codex/reports/phase33-windows-build-preflight.json
   ```
3. Run the aggregate smoke report:
   ```bash
   python .codex/scripts/deimos_windows_release_smoke.py . .codex/reports/phase33-windows-release-smoke.json
   ```
4. On Windows, build with:
   ```bash
   uv run --group dev pyinstaller --noconfirm --clean Deimos.spec
   ```
5. After building, require the release artifact:
   ```bash
   python .codex/scripts/deimos_release_artifact_report.py . .codex/reports/phase33-release-artifact-report.json --require-artifact
   ```

Do not claim a release is ready if the required artifact report has blockers.
