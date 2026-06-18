# Enemy Bot Impact Workflow

Use when a Deimos change touches enemy targeting, boss farming, quest combat, zone bots, deck assumptions, or drop/farming recommendations.

1. Identify the target world, zone, enemy, boss, quest, or farming goal.
2. Query local Wizard101 data first:

```bash
python .codex/tools/query_wizard101_data.py data/wizard101 --kind enemy --q "<enemy or zone>"
```

3. Run or emulate the enemy impact report:

```bash
python scripts/bot_enemy_impact_report.py data/wizard101 --zone "<zone>"
```

4. Treat missing school, spells, cheats, or drops as unverified. Add fallback behavior instead of hard-coding assumptions.
5. For bosses, skeleton key bosses, dungeons, gauntlets, raids, and event creatures, require a strategy/automation review before recommending default bots.
6. Update localization and UI text if the user-visible bot result includes risk labels.
