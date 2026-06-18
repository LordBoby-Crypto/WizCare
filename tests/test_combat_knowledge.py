from src.combat_knowledge import CombatKnowledgeAdvisor
from src.wizard101_knowledge import Wizard101KnowledgeCatalog


def test_combat_advisor_falls_back_for_unknown_enemy():
    advisor = CombatKnowledgeAdvisor(Wizard101KnowledgeCatalog())
    plan = advisor.explain_for_enemy_names(["Lost Soul"])
    assert plan["strategy_unlocked"] is False
    assert plan["use_generic_safe_config"] is True
    assert "Unknown enemy 'Lost Soul'" in plan["notes"][0]
