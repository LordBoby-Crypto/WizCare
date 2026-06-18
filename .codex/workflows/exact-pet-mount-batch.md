# Exact Pet/Mount Batch Workflow

Use this workflow when Codex modifies pet, mount, collection, drop, or farming-route logic.

1. Check whether the pet or mount record is exact-page core-ready.
2. If exact page is blocked or unverified, keep all stats/talents/speed/meta claims locked.
3. For exact pets, allow factual lookup fields only.
4. For exact mounts, allow speed/stat facts only if the exact mount page was imported.
5. Do not create best-pet, hatch-value, or best-mount claims without strategy-reviewed comparison data.
6. Run `pet_mount_phase17_status_report.py`, `pet_meta_unlock_matrix.py`, and `blocked_exact_page_retry_queue.py`.
