# Phase 35 release upload safety

Codex must preserve updater-compatible release artifacts. Do not rename the raw release assets unless updater code and documentation are updated in the same change.

Required raw release assets:

- `dist/Deimos.exe`
- `dist/Deimos.exe.sha256`
- `dist/release-manifest.json`

Checksum file format:

```text
<64-hex-sha256>  Deimos.exe
```

Manifest requirements:

- `application` must be `Deimos`.
- `manifest_schema_version` should be present.
- `artifacts` must include `Deimos.exe`, `Deimos.exe.sha256`, and `release-manifest.json`.
- `release_requirements` must include the same three names.
- `updater_contract` should document stable asset names and checksum format.

Treat missing `dist/Deimos.exe` as a warning during pre-build checks and as a blocker during post-build/release checks.
