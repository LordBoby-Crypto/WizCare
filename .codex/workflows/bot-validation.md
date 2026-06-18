# Bot Validation Workflow

Use this before modifying or generating Deimos bot logic.

1. Identify world, zone, quest, enemy, boss, drops, or farming goal.
2. Query local Wizard101 data for zone/enemy/quest/cheat/drop facts.
3. Confirm whether the area is overland, dungeon, gauntlet, sigil-gated, solo-only, or teleport-limited.
4. Check enemy school, spells used, cheats, and required counter-strategy.
5. Flag unverified or missing records before making code assumptions.
6. Make the smallest repo change and run static validators.
