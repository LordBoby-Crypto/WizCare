# Jewel/Reagent Validation Workflow

Use for Deimos changes involving jewels, reagents, loot routing, or farming recommendations.

1. Identify the source creature/boss and tier.
2. Check typed `jewels.json` and `reagents.json` records.
3. Run `jewel_socket_guardrail_report.py` and `reagent_crafting_gap_report.py`.
4. Do not recommend best jewels without exact jewel page and equip/socket rules.
5. Do not recommend reagent farming routes without crafting-use and route-efficiency data.
6. Report missing data as a blocker instead of guessing.
