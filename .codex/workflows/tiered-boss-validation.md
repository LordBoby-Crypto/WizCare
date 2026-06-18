# Tiered Boss Validation Workflow

Use this workflow whenever Deimos code, bots, or farming logic touches tiered bosses such as King Borr or Lambent Fire.

1. Query the exact tier record. Do not use a disambiguation page as combat data.
2. Confirm the wizard level range and drop level gate.
3. Review cheat triggers before deck or bot sequencing.
4. Reject generic route logic if late-join, Feint/trap/blade, minion-resummon, or same-round defeat cheats are present.
5. Run `tiered_boss_matrix.py`, `tiered_boss_gap_report.py`, and `tiered_boss_bot_rules.py`.
6. Mark any route that has not been manually smoke-tested as `manual-review-required`.
