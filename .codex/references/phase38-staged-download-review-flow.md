# Phase 38 - Staged download review flow

Phase 38 adds a manual, review-first path for downloading update assets to a user-selected staging folder. The flow must verify `Deimos.exe` using `Deimos.exe.sha256` and may download `release-manifest.json`, but it must never replace the running executable, relaunch Deimos, or silently install updates.

## Allowed behavior

- Check GitHub Releases metadata.
- Show stable asset availability.
- Let the user choose a staging folder.
- Download `Deimos.exe`, `Deimos.exe.sha256`, and optionally `release-manifest.json`.
- Verify SHA-256 before reporting success.

## Locked behavior

- No automatic install.
- No `os.replace`/`shutil.move` over the live executable.
- No relaunch helper.
- No startup/background download.

## Required checks

Run:

```bash
python .codex/scripts/deimos_phase38_staged_download_readiness.py .
```
