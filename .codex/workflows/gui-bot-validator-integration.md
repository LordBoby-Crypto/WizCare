# GUI Bot Validator Integration Workflow

Use this workflow when Codex changes the Deimos bot editor, bot import/export, run button behavior, parser validation, or user-facing bot validation messages.

1. Inspect `src/gui/tab_actions.py`, especially `build_bot_tab` and `run_bot_callback`.
2. Inspect `src/gui/commands.py` for `GUICommandType.ExecuteBot` and `GUICommandType.KillBot`.
3. Run the GUI bot editor integration report.
4. Run the GUI validation message contract report.
5. If adding strings, update every `.lang` file together.
6. Keep parser errors, Wizard101 knowledge warnings, and strategy/meta warnings separate.
7. Never execute bot text during validation.
8. Run parser-aware bot validation after the patch.

Recommended commands:

```bash
python .codex/scripts/deimos_gui_bot_editor_integration_report.py . .codex/reports/gui_bot_editor_integration.json
python .codex/scripts/deimos_gui_validation_message_contract.py . .codex/reports/gui_validation_messages.json
python .codex/scripts/deimos_gui_command_surface_guardrail.py . .codex/reports/gui_command_surface.json
python .codex/scripts/deimos_gui_validation_patch_plan.py . .codex/reports/gui_validation_patch_plan.md
python .codex/scripts/deimos_parser_aware_bot_validator.py . .codex/reports/parser_aware_bot_validation.json
```
