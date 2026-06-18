# Parser validator deepening workflow

Run these from the full Deimos repo after applying repo-copy files.

```bash
python skills/deimos-wizard101-engineer/scripts/deimoslang_static_contract_report.py . .codex/reports/deimoslang-contract.json
python skills/deimos-wizard101-engineer/scripts/deimos_raw_bot_validator.py . path/to/bot.txt .codex/reports/raw-bot-validation.json
python skills/deimos-wizard101-engineer/scripts/deimos_combat_config_marker_validator.py path/to/playstyle.txt .codex/reports/combat-marker-validation.json
python skills/deimos-wizard101-engineer/scripts/deimos_zone_alias_validator.py . path/to/zones.txt .codex/reports/zone-alias-validation.json
```

Use this before changing raw bot scripts, DeimosLang features, route commands, combat config markers, or GUI bot editor behavior.
