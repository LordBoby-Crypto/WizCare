# Non-gear loot validation workflow

Use this before Deimos/Codex changes that recommend farming for spellements, keys, jewels, reagents, treasure cards, or housing drops.

1. Query drops for the boss/source.
2. Filter by `item_type`; do not mix non-gear goals with gear ranking.
3. Run `king_borr_loot_type_coverage_report.py` for King Borr work.
4. Run `spellement_quantity_matrix.py` for King Borr spellement work.
5. Keep all route recommendations guarded unless strategy-reviewed route efficiency exists.
6. Show level-gate and Participation Trophy warnings when King Borr Tier 1 is involved.
