# Wizard101 knowledge roadmap

The project goal is a complete working Deimos/WizCare assistant that can improve combat, bots, routing, gear decisions, and other automation with verified Wizard101 facts.

## Non-negotiable completion target

The project is not allowed to claim it knows Wizard101 completely until every required dataset in `data/wizard101/catalog_manifest.json` is populated and verified. That includes every equipable item, every enemy, every spell, every stat/pip rule, every quest, every world/zone, every NPC, every pet, every mount, every jewel, and every reagent that can affect automation decisions.

## Data policy

Do not guess Wizard101 facts. The knowledge catalog must store missing data as missing until it is source-linked and verified. Enemy-specific combat choices require exact enemy records, and recommended strategies require `strategy-reviewed` records.

## Catalog datasets

- `data/wizard101/enemies.jsonl`: every enemy, boss, minion, school, health, resists, boosts, cheats, spell tendencies, drops, locations, and source metadata.
- `data/wizard101/gear.jsonl`: every attachable/equipable item including hat, robe, boots, wand, athame, amulet, ring, deck, pet, mount, jewels, elixirs, requirements, stats, sockets, set bonuses, restrictions, and exact source metadata.
- `data/wizard101/spells.jsonl`: every trained spell, item card, treasure card, enemy-only spell, spellement path, effect model, pip cost, school, targeting, and exact source metadata.
- `data/wizard101/stats.jsonl`: every character stat and combat stat including damage, resist, pierce, accuracy, crit, block, healing, pip conversion, archmastery, health, mana, energy, and speed formulas.
- `data/wizard101/pip_system.jsonl`: normal pips, power pips, school pips, shadow pips, archmastery, pip conversion, starting pips, enemy pip rules, and spell cost rules.
- `data/wizard101/quests.jsonl`: every quest, prerequisite, objective, NPC, zone transition, reward, and automation-relevant edge case.
- `data/wizard101/worlds.jsonl`, `npcs.jsonl`, `pets.jsonl`, `mounts.jsonl`, `jewels.jsonl`, and `reagents.jsonl`: supporting game facts that combat and bot logic need.

## Auto-combat integration path

1. Load verified enemy facts from `src.wizard101_knowledge.Wizard101KnowledgeCatalog`.
2. When an enemy is unknown, use the current generic-safe combat config.
3. When an enemy is exact-page verified, allow enemy-aware safety constraints such as school/resist/cheat warnings.
4. When an enemy is strategy-reviewed, allow enemy-specific combat configuration recommendations.
5. Use verified spell, stat, pip, and gear records to score candidate cards and team roles.
6. Record all unresolved facts in coverage reports before claiming a feature is complete.

## Current combat work

The combat path now has a `CombatKnowledgeAdvisor` bridge. It explains whether detected enemies are unknown, known-but-not-strategy-reviewed, or strategy-unlocked. Auto-combat must keep using the generic-safe config until enemy, spell, stat, pip, and gear facts are verified enough to unlock enemy-specific strategy.

## Raw ingestion path

The project now has `scripts/wizard101_ingest_mediawiki.py` for source-linked raw category ingestion. Raw ingested records are not trusted for strategy by themselves; they are staging inputs that must be normalized into dataset records and manually/automatically verified before auto-combat can use them.

## Completion definition

The project is not complete until the catalog is populated, validated, and connected to combat/bot decisions with tests that prove unknown facts fall back safely instead of being guessed.
