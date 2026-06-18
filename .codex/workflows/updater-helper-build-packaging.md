# Phase 43 - Updater Helper Build Packaging Scaffold

Use this workflow before building or reviewing the future updater helper executable.

## Commands

```bash
python .codex/scripts/deimos_phase43_update_helper_build_readiness.py . .codex/reports/phase43-update-helper-build-readiness.json
```

Optional helper preflight:

```bash
python libs/updater_helper/build_helper.py --report .codex/reports/phase43-build-helper-preflight.json
```

Optional actual helper build on a properly prepared Windows build machine:

```bash
cd libs/updater_helper
uv run --group dev pyinstaller --noconfirm --clean deimos_updater_helper.spec
```

## Locked behavior

The GUI must not launch this helper yet. The helper must remain dry-run-only. Do not replace `Deimos.exe`, relaunch Deimos, or perform automatic installation in Phase 43.
