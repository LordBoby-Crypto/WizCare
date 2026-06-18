# Pet/Mount Validation Workflow

Use this workflow before Deimos/Codex claims a boss is good for pet or mount farming.

1. Query `pets.json`, `mounts.json`, and `drops.json` for the boss.
2. Confirm whether the record is only a visible drop-table row or an exact pet/mount page import.
3. If exact page details are missing, label the recommendation as collection-only.
4. Do not mention talents, hatch value, item cards, speed, or stat bonuses unless the exact page record is imported.
5. Run:

```bash
python scripts/pet_mount_collection_report.py data/wizard101
python scripts/pet_talent_gap_report.py data/wizard101
python scripts/mount_speed_stat_gap_report.py data/wizard101
python scripts/collection_goal_guardrail_report.py data/wizard101
```
