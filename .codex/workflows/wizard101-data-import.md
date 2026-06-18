# Wizard101 Data Import Workflow

1. Put user/public/source records in JSON or JSONL format.
2. Import records:

```bash
python skills/deimos-wizard101-engineer/scripts/import_records.py input.json --kind enemy --out skills/deimos-wizard101-engineer/data/wizard101 --source-name "User curated" --source-kind user_json
```

3. Normalize:

```bash
python skills/deimos-wizard101-engineer/scripts/normalize_wizard101_records.py skills/deimos-wizard101-engineer/data/wizard101
```

4. Validate, index, and report coverage:

```bash
python skills/deimos-wizard101-engineer/scripts/validate_wizard101_data.py skills/deimos-wizard101-engineer/data/wizard101
python skills/deimos-wizard101-engineer/scripts/build_wizard101_index.py skills/deimos-wizard101-engineer/data/wizard101
python skills/deimos-wizard101-engineer/scripts/coverage_report.py skills/deimos-wizard101-engineer/data/wizard101
```
