# Exact Gear Batch Workflow

Use this workflow when Codex imports or edits exact item-stat records.

1. Verify the exact item page source.
2. Record item type, level requirement, stats, item cards, trade flags, and sources.
3. Add exact drop links only when source pages support them.
4. Run data validation and item-stat reports.
5. Keep best-gear ranking locked unless comparison buckets are sufficiently populated and strategy-reviewed.

Required scripts:

```bash
python scripts/validate_wizard101_data.py data/wizard101
python scripts/item_stat_batch_report.py data/wizard101
python scripts/gear_school_coverage_report.py data/wizard101
python scripts/boss_drop_completion_report.py data/wizard101 --boss "King Borr"
python scripts/best_gear_unlock_matrix.py data/wizard101
```
