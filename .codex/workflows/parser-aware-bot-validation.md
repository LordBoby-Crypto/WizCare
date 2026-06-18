# Parser-aware bot validation workflow

Run this before changing Deimos bot scripts, DeimosLang support, raw command parsing, combat config parsing, or route/pathing behavior.

1. Build/update the command contract:

```bash
python .codex/scripts/deimos_command_argument_contract.py . .codex/reports/command-argument-contract.json
```

2. Validate bot-like files:

```bash
python .codex/scripts/deimos_parser_aware_bot_validator.py . .codex/reports/parser-aware-bot-validator.json
```

3. Check traversal/Wizard101 links:

```bash
python .codex/scripts/deimos_zone_entity_link_validator.py . .codex/data/wizard101 .codex/reports/zone-entity-link-validator.json
```

4. Check combat marker coverage:

```bash
python .codex/scripts/deimos_combat_marker_coverage.py . .codex/reports/combat-marker-coverage.json
```

5. Treat parser errors as blockers. Treat warnings as manual review prompts.

Do not claim route or combat correctness solely from parser success. Route/combat correctness also requires Wizard101 data maturity for zones, enemies, bosses, cheats, drops, and quest state.
