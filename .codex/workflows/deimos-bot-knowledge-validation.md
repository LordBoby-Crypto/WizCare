# Deimos bot knowledge validation workflow

Use this workflow before changing Deimos bot, route, quest, farm, combat, or deck logic.

## Steps

1. Run a bot inventory:

```bash
python skills/deimos-wizard101-engineer/scripts/deimos_bot_inventory.py . --out .codex/reports/bot-inventory.json
```

2. Link bot files to Wizard101 knowledge:

```bash
python skills/deimos-wizard101-engineer/scripts/deimos_bot_w101_link_report.py . skills/deimos-wizard101-engineer/data/wizard101 --out .codex/reports/bot-w101-link-report.json
```

3. Run guardrails:

```bash
python skills/deimos-wizard101-engineer/scripts/deimos_bot_guardrail_report.py . skills/deimos-wizard101-engineer/data/wizard101 --out .codex/reports/bot-guardrail-report.json
```

4. If blockers appear, enrich Wizard101 data or narrow the code change before editing gameplay behavior.

## Allowed when unresolved

- Add TODO comments.
- Add safer errors/warnings.
- Improve UI plumbing.
- Add validation checks.

## Not allowed when unresolved

- Claim a bot fully supports a boss/zone.
- Generate a full combat rotation.
- Recommend farming routes.
- Claim best spells, best drops, or best gear.
