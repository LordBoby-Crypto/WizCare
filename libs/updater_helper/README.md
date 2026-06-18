# Deimos updater helper scaffold

Phase 42 adds a non-integrated helper scaffold. It validates helper manifests and supports dry-run planning only. It must not replace `Deimos.exe`, relaunch Deimos, or perform installation until a later reviewed implementation phase explicitly enables that behavior.

Example dry run:

```bash
python libs/updater_helper/deimos_updater_helper.py --manifest path/to/deimos-helper-manifest.json --wait-pid 1234 --log helper.log --dry-run
```


## Phase 43 helper build packaging scaffold

The helper now includes a PyInstaller build scaffold:

```bash
cd libs/updater_helper
uv run --group dev pyinstaller --noconfirm --clean deimos_updater_helper.spec
```

Preflight without building:

```bash
python build_helper.py --report ../../.codex/reports/phase43-helper-build-preflight.json
```

The resulting helper executable is still **not launched by the GUI** and the helper remains dry-run-only until a future reviewed install phase.
