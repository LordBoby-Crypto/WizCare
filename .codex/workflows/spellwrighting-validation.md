# Spellwrighting Validation Workflow

Use this workflow when adding spell, spellement, item-card, or bot-rotation logic.

1. Query `spells.json` for the exact spell record.
2. Query `spellwrighting.json` for visible tier thresholds.
3. Query `spell_links.json` for source relationships such as boss spellement drops or pet item cards.
4. Run `scripts/spellwrighting_track_report.py`.
5. Run `scripts/spellement_source_matrix.py`.
6. Run `scripts/spellwrighting_strategy_lock_report.py`.
7. Do not generate bot rotations, PvP advice, or upgrade-path recommendations unless a strategy-reviewed record unlocks it.
