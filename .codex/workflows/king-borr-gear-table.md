# King Borr gear-table workflow

When changing Deimos logic that references King Borr drops or low-level gear:

1. Query the Wizard101 data for King Borr Tier 1 drop records.
2. Separate drop-table records from exact stat-ready gear records.
3. Run `king_borr_tier1_gear_table_report.py`.
4. Run `gear_comparison_bucket_report.py`.
5. Do not expose best-gear recommendations unless the bucket report unlocks that exact bucket and a strategy review exists.
6. Preserve level-gate and skeleton-key warnings in user-facing recommendations.
