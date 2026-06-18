# Spell strategy scaffolding workflow

Use this workflow when Codex is asked to use Wizard101 spell data for Deimos bots, spell displays, spellwrighting routes, or combat strategy.

1. Query exact spell records and spell links.
2. Check `pvp_status`, school pip requirements, trainability, item-card source, and spellwrighting data.
3. Run `spell_strategy_scaffold_report.py`.
4. Run `spell_pve_pvp_lock_matrix.py`.
5. Run `spell_bot_usage_guardrail_report.py`.
6. If a requested claim is locked, say exactly what data is missing instead of guessing.
7. Only modify Deimos bot/casting logic when a strategy-reviewed record unlocks that specific use case.
