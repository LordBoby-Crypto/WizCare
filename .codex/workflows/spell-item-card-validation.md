# Spell and Item-Card Validation Workflow

Use this workflow when changing Deimos features related to pets, item cards, spells, spellements, combat logic, farming routes, or bot recommendations.

1. Query `spells.json` for the spell.
2. Check `data_quality.exact_spell_page_verified`.
3. Query `spell_links.json` for item-card or boss-spellement relationships.
4. Run `scripts/spell_exact_readiness_report.py data/wizard101`.
5. Run `scripts/spell_item_card_link_report.py data/wizard101`.
6. Run `scripts/spell_strategy_guardrail_report.py data/wizard101`.
7. Only use exact facts for display/validation unless a strategy-reviewed record unlocks recommendations.
