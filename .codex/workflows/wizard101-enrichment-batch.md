# Wizard101 Enrichment Batch Workflow

Use this when expanding the Wizard101 knowledge database for Deimos/Codex work.

1. Build a queue of records that need enrichment.

```bash
python scripts/build_enrichment_queue.py data/wizard101 --kind enemies --limit 25 --out queue/enemies-next.json
```

2. Fetch snapshots locally if network access is available.

```bash
python scripts/import_mediawiki_page_snapshots.py --titles queue/enemies-next.json --out snapshots/enemies --limit 25
```

3. Attach or import snapshots into the relevant records, then run conservative enrichment.

```bash
python scripts/enrich_creature_records.py data/wizard101
python scripts/promote_data_maturity.py data/wizard101 --out reports/maturity.json
```

4. Run quality reports.

```bash
python scripts/creature_gap_report.py data/wizard101 --out reports/creature-gaps.json
python scripts/source_audit_report.py data/wizard101 --out reports/source-audit.json
python scripts/wizard101_batch_status.py data/wizard101 --out reports/batch-status.json
```

5. Rebuild indexes.

```bash
python scripts/build_wizard101_index.py data/wizard101
python scripts/build_alias_index.py data/wizard101
```

Do not allow Codex to use `stub` or weak `partial` records for hard automation decisions.
