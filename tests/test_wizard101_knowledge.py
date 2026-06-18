from src.wizard101_knowledge import Wizard101KnowledgeCatalog


def test_empty_catalog_reports_safe_unknown_enemy():
    catalog = Wizard101KnowledgeCatalog()
    context = catalog.get_enemy_combat_context("Lost Soul")
    assert context["known"] is False
    assert context["strategy_unlocked"] is False
    assert context.get("recommended_policy", "generic-safe") == "generic-safe"


def test_catalog_files_are_present_issue_free_and_incomplete():
    catalog = Wizard101KnowledgeCatalog()
    report = catalog.coverage_report()
    assert report["schema_version"] == "wizard101-knowledge-v1"
    assert report["issues"] == []
    assert report["complete"] is False
    assert set(report["missing_datasets"]) == set(report["counts"])
    assert {"enemies", "gear", "spells", "pip_system", "stats"}.issubset(report["counts"])


def test_manifest_declares_full_game_domains_and_slots():
    catalog = Wizard101KnowledgeCatalog()
    manifest = catalog.manifest
    assert {"hat", "robe", "boots", "wand", "athame", "amulet", "ring", "deck"}.issubset(manifest["equipment_slots"])
    assert {"damage", "critical", "resistance", "power_pip_chance", "archmastery"}.issubset(manifest["combat_stat_categories"])
    assert manifest["coverage_targets"]["enemies"]["minimum_verification"] == "strategy-reviewed"
    assert manifest["coverage_targets"]["spells"]["minimum_verification"] == "strategy-reviewed"
