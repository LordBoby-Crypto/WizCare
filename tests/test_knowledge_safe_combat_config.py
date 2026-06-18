import pytest

pytest.importorskip("wizwalker")

from src.config_combat import build_knowledge_safe_combat_config, default_config
from src.wizard101_knowledge import Wizard101KnowledgeCatalog


def test_knowledge_safe_config_keeps_default_for_unknown_enemy():
    config, explanation = build_knowledge_safe_combat_config(["Lost Soul"], Wizard101KnowledgeCatalog())
    assert config == default_config
    assert explanation["use_generic_safe_config"] is True
    assert explanation["strategy_unlocked"] is False
