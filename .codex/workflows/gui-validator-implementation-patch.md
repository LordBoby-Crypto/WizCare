# GUI validator implementation workflow

Use this workflow when adding or reviewing the Phase 28 bot validation patch in the Deimos repo.

1. Copy `patches/phase28/src/gui/bot_validation.py` to `src/gui/bot_validation.py`.
2. Apply the `tab_actions.py` changes or replace the file with `patches/phase28/src/gui/tab_actions.py` only if the target file still matches the main baseline structure.
3. Append `patches/phase28/locale/en.lang.append` and `patches/phase28/locale/zh.lang.append`.
4. Run:
   ```bash
   python -m py_compile src/gui/bot_validation.py
   python .codex/scripts/deimos_gui_validation_patch_static_check.py . --out .codex/reports/phase28_gui_validator_static_check.json
   ```
5. Manually test the Bot tab:
   - empty script should block,
   - unknown command should warn,
   - warning-only script should ask before running,
   - valid simple script should queue ExecuteBot.
