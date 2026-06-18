"""Knowledge-aware auto-combat planning helpers.

The advisor does not replace the existing combat backend yet. It provides a safe
bridge from detected enemies to verified Wizard101 facts so future combat logic
can improve without guessing unknown enemy, spell, stat, or cheat behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from src.wizard101_knowledge import Wizard101KnowledgeCatalog, load_default_catalog


@dataclass(frozen=True)
class CombatKnowledgePlan:
    enemy_contexts: list[dict[str, Any]]
    use_generic_safe_config: bool
    strategy_unlocked: bool
    notes: list[str]


class CombatKnowledgeAdvisor:
    """Build conservative combat notes from verified Wizard101 knowledge."""

    def __init__(self, catalog: Wizard101KnowledgeCatalog | None = None):
        self.catalog = catalog if catalog is not None else load_default_catalog()

    def plan_for_enemy_names(self, enemy_names: Iterable[str]) -> CombatKnowledgePlan:
        contexts = [self.catalog.get_enemy_combat_context(name) for name in enemy_names]
        unknown = [ctx for ctx in contexts if not ctx.get("known")]
        locked = [ctx for ctx in contexts if ctx.get("known") and not ctx.get("strategy_unlocked")]
        strategy_unlocked = bool(contexts) and not unknown and not locked
        notes: list[str] = []
        for ctx in unknown:
            notes.append(f"Unknown enemy '{ctx['enemy_name']}'; use generic-safe combat config.")
        for ctx in locked:
            notes.append(
                f"Enemy '{ctx['enemy_name']}' is known but not strategy-reviewed; avoid enemy-specific automation."
            )
        for ctx in contexts:
            cheats = ctx.get("cheats") or []
            if cheats:
                notes.append(f"Enemy '{ctx['enemy_name']}' has recorded cheats: {', '.join(map(str, cheats))}")
            school = ctx.get("school")
            if school:
                notes.append(f"Enemy '{ctx['enemy_name']}' school: {school}")
        return CombatKnowledgePlan(
            enemy_contexts=contexts,
            use_generic_safe_config=not strategy_unlocked,
            strategy_unlocked=strategy_unlocked,
            notes=notes,
        )

    def explain_for_enemy_names(self, enemy_names: Iterable[str]) -> dict[str, Any]:
        plan = self.plan_for_enemy_names(enemy_names)
        return {
            "strategy_unlocked": plan.strategy_unlocked,
            "use_generic_safe_config": plan.use_generic_safe_config,
            "enemy_contexts": plan.enemy_contexts,
            "notes": plan.notes,
        }
