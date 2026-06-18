# Exact Item Stat Enrichment Workflow

Use this when adding Wizard101 gear/item facts for Deimos.

1. Open the exact Wizard101 Central `Item:` page.
2. Record the source URL and retrieved date.
3. Extract level requirement, type, bonus lines, item cards, trade flags, and drop sources.
4. Normalize only fields that are visibly present.
5. Set `stat_profile_status`:
   - `stat-ready` for concrete numeric bonuses
   - `no-stats-listed` when the page lists no numeric combat bonuses
   - `needs-review` when page text is ambiguous
6. Keep `best_gear_status = blocked` unless a ranking/reference explicitly supports it.
7. Run:
   ```bash
   python scripts/item_stat_readiness_report.py data/wizard101/seed/gear.json --output item-stat-readiness.json
   python scripts/best_gear_candidate_matrix.py data/wizard101/seed/gear.json --output best-gear-candidate-matrix.json
   ```
