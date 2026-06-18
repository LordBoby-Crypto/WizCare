# Wizard101 bulk ingestion workflow

Use this workflow when expanding the Wizard101 database.

1. Pick one collection, such as `enemies`, `quests`, `gear`, or `spells`.
2. Run or prepare category-member import to create source-tracked stubs.
3. Normalize names and aliases.
4. Enrich only a small verified slice at a time.
5. Run validation, alias index, relation validation, coverage matrix, and search index rebuild.
6. Never mark a category complete unless the coverage report and manual review support that claim.

Recommended commands from the skill folder:

```bash
python scripts/generate_import_manifest.py data/wizard101
python scripts/import_mediawiki_category_members.py --api https://wiki.wizard101central.com/wiki/api.php --category "Creatures" --kind enemy --out data/wizard101 --limit 500
python scripts/normalize_wizard101_records.py data/wizard101
python scripts/build_alias_index.py data/wizard101
python scripts/validate_relations.py data/wizard101
python scripts/entity_coverage_matrix.py data/wizard101
python scripts/build_wizard101_index.py data/wizard101
```
