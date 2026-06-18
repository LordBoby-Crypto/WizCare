# Creature Page Enrichment Workflow

Use when updating Deimos with enemy/boss knowledge.

1. Run `python scripts/creature_priority_queue.py data/wizard101 --limit 50 --out reports/creature-priority.json`.
2. Pick high-impact bosses, skeleton key bosses, cheating bosses, spellement-dropping creatures, and farm targets first.
3. Fetch or paste a source page.
4. Draft extraction with `extract_creature_fields_template.py`, then manually verify all fields.
5. Merge with `merge_creature_enrichment.py`.
6. Run validation, readiness report, source audit, alias index, relation validation, and search-index rebuild.
7. Only use records marked `combat-core-ready` or better for bot risk logic.
