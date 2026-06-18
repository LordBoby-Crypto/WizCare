# Drop/Gear Enrichment Workflow

Use this workflow when adding or using Wizard101 drop, gear, spellement, or farming-route data.

1. Import or verify the source page for the boss/item.
2. Create drop records for source-listed items or families.
3. Create gear records only when the item/family source is clear.
4. Mark family-level records as not usable for best-gear rankings.
5. Run `drop_gear_link_report.py` and `gear_stat_gap_report.py`.
6. For Deimos bot features, run `boss_farming_route_report.py` and block automation if cheats/tier/key requirements are unresolved.

Never let Codex present family-level records as exact item-stat knowledge.
