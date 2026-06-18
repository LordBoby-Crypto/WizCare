# Phase 68 - Diagnostics report import GUI polish

Adds a safe GUI import/review flow for exported diagnostics comparison report bundles.

## Safety contract

- Review only.
- Executable payload import remains blocked.
- Helper launch remains blocked.
- Install execution remains blocked.
- Non-dry-run update behavior remains blocked.

## Accepted bundle

The imported ZIP must be a comparison report export containing `README.txt`, `comparison-review.json`, `comparison-report.json`, `source-summaries.json`, and `export-metadata.json`. The import inspector rejects `Deimos.exe`, updater helper executables, scripts, DLLs, installers, and other executable payloads.
