# Wizard101 boss safety workflow

Use this workflow before Codex changes any Deimos bot/farming/combat logic that depends on a boss, enemy, dungeon, skeleton key, raid, or gauntlet.

1. Query the Wizard101 data index for the target boss/enemy.
2. Check `bot_readiness`. Do not use `sourced-stub`, `disambiguation-only`, or `category-summary-only` for gameplay logic.
3. Run `boss_priority_report.py`, `cheat_gap_report.py`, and `boss_bot_safety_matrix.py` when boss data is relevant.
4. If cheats exist, review trigger/effect/counter fields before generating or editing bot behavior.
5. If the boss is tiered, enrich the exact tier page before strategy work.
6. If drops or farming value are relevant, require a drop-source or strategy record; do not infer value from category membership.
