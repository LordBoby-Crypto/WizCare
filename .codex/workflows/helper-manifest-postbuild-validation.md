# Helper Manifest Post-Build Validation

Use this workflow after Windows build artifacts exist.

1. Build Deimos with `Deimos.spec`.
2. Build updater helper with `libs/updater_helper/deimos_updater_helper.spec`.
3. Generate checksums and manifest:

```bash
python .codex/scripts/deimos_checksum_release_artifacts.py . .codex/reports/release-checksum-report.json --write --require-artifact --require-helper-artifact
```

4. Validate strict post-build metadata:

```bash
python .codex/scripts/deimos_phase48_manifest_postbuild_readiness.py . .codex/reports/phase48-manifest-postbuild-readiness.json --strict-postbuild
```

Do not enable helper launch or install execution unless a later phase explicitly implements and validates that path.
