# Deimos Codex Commands

Suggested local commands when the plugin is installed nearby:

```bash
python skills/deimos-wizard101-engineer/scripts/index_repo.py .
python skills/deimos-wizard101-engineer/scripts/check_locale_keys.py .
python skills/deimos-wizard101-engineer/scripts/check_version_consistency.py .
python skills/deimos-wizard101-engineer/scripts/check_release_readiness.py .
python skills/deimos-wizard101-engineer/scripts/coverage_report.py skills/deimos-wizard101-engineer/data/wizard101
python skills/deimos-wizard101-engineer/scripts/build_wizard101_index.py skills/deimos-wizard101-engineer/data/wizard101
```

- `/w101.boss-safety <boss>`: inspect boss readiness, cheats, access constraints, and Deimos bot risks before editing automation.
## Phase 21 spell strategy commands

- `/w101.spell-strategy-check` - run spell strategy scaffold, PvE/PvP lock, and bot usage guardrail reports.
- `/deimos.bot-spell-policy-check` - verify a Deimos bot/spell change has exact facts, context, and strategy-reviewed unlock records before using spell data for automation.

## Phase 22 Deimos integration hooks

```bash
python skills/deimos-wizard101-engineer/scripts/deimos_repo_knowledge_health.py .
python skills/deimos-wizard101-engineer/scripts/deimos_bot_inventory.py .
python skills/deimos-wizard101-engineer/scripts/deimos_bot_w101_link_report.py . skills/deimos-wizard101-engineer/data/wizard101
python skills/deimos-wizard101-engineer/scripts/deimos_bot_guardrail_report.py . skills/deimos-wizard101-engineer/data/wizard101
```


## Phase 24 full repo adapter commands

```bash
python skills/deimos-wizard101-engineer/scripts/deimos_full_repo_adapter_report.py . .codex/reports/full-repo-adapter.json
python skills/deimos-wizard101-engineer/scripts/deimos_command_surface_report.py . .codex/reports/command-surface.json
python skills/deimos-wizard101-engineer/scripts/deimos_traversal_w101_link_report.py . .codex/reports/traversal-w101-links.json
python skills/deimos-wizard101-engineer/scripts/deimos_release_locale_full_repo_report.py . .codex/reports/release-locale.json
```

## Phase 25 parser validator commands

```bash
python skills/deimos-wizard101-engineer/scripts/deimoslang_static_contract_report.py . .codex/reports/deimoslang-contract.json
python skills/deimos-wizard101-engineer/scripts/deimos_raw_bot_validator.py . path/to/bot.txt .codex/reports/raw-bot-validation.json
python skills/deimos-wizard101-engineer/scripts/deimos_combat_config_marker_validator.py path/to/playstyle.txt .codex/reports/combat-marker-validation.json
python skills/deimos-wizard101-engineer/scripts/deimos_zone_alias_validator.py . path/to/zones.txt .codex/reports/zone-alias-validation.json
```



## Phase 26 parser-aware validation commands

```bash
python .codex/scripts/deimos_command_argument_contract.py . .codex/reports/command-argument-contract.json
python .codex/scripts/deimos_parser_aware_bot_validator.py . .codex/reports/parser-aware-bot-validator.json
python .codex/scripts/deimos_zone_entity_link_validator.py . .codex/data/wizard101 .codex/reports/zone-entity-link-validator.json
python .codex/scripts/deimos_combat_marker_coverage.py . .codex/reports/combat-marker-coverage.json
```

## Phase 35 release upload safety

```bash
python .codex/scripts/deimos_release_upload_safety.py . .codex/reports/phase35-release-upload-safety.json
python .codex/scripts/deimos_release_upload_safety.py . .codex/reports/phase35-release-upload-safety-postbuild.json --require-artifact
```

## Phase 40 install design

```bash
python .codex/scripts/deimos_phase40_install_design_readiness.py . .codex/reports/phase40-install-design-readiness.json
```

## Phase 42 updater helper scaffold

```bash
python .codex/scripts/deimos_phase42_update_helper_readiness.py .
```

Use this before changing updater-helper code. Phase 42 is dry-run only.

## Phase 48 manifest post-build validation

```bash
python .codex/scripts/deimos_phase48_manifest_postbuild_readiness.py . .codex/reports/phase48-manifest-postbuild-readiness.json
python .codex/scripts/deimos_phase48_manifest_postbuild_readiness.py . .codex/reports/phase48-manifest-postbuild-readiness.json --strict-postbuild
```

## Phase 49 dry-run release simulation

```bash
python .codex/scripts/deimos_phase49_release_simulation_readiness.py . .codex/reports/phase49-release-simulation-readiness.json
```


## Phase 61 - Diagnostics comparison report

```bash
python .codex/scripts/deimos_staged_update_diagnostics_import.py bundle.zip report.json
python .codex/scripts/deimos_staged_update_diagnostics_comparison.py before.zip after.zip comparison.json
python .codex/scripts/deimos_phase61_diagnostics_comparison_readiness.py
```


### Phase 62 diagnostics comparison GUI/report polish

```bash
python .codex/scripts/deimos_staged_update_diagnostics_comparison_review.py before.zip after.zip .codex/reports/phase62-comparison-review.json
python .codex/scripts/deimos_phase62_diagnostics_comparison_review_readiness.py
```


### Phase 63 diagnostics comparison GUI action scaffold

```bash
python .codex/scripts/deimos_diagnostics_comparison_gui_action_contract.py
python .codex/scripts/deimos_phase63_diagnostics_comparison_gui_action_readiness.py
```

## Phase 64 - diagnostics comparison menu/button wiring

```bash
python .codex/scripts/deimos_diagnostics_comparison_gui_wiring_contract.py
python .codex/scripts/deimos_diagnostics_comparison_gui_wiring_smoke.py
python .codex/scripts/deimos_phase64_diagnostics_comparison_gui_wiring_readiness.py
```

These checks confirm the `Compare diagnostics` GUI action is wired to the safe read-only diagnostics comparison dialog and does not enable install behavior.

## Phase 65 diagnostics comparison export/share checks

```bash
python .codex/scripts/deimos_diagnostics_comparison_export_contract.py
python .codex/scripts/deimos_diagnostics_comparison_export_smoke.py
python .codex/scripts/deimos_phase65_diagnostics_comparison_export_readiness.py
```

Export a safe comparison report bundle:

```bash
python .codex/scripts/deimos_diagnostics_comparison_export.py before-diagnostics.zip after-diagnostics.zip deimos-diagnostics-comparison-report.zip
```


## Phase 66 diagnostics comparison export GUI polish

```bash
python .codex/scripts/deimos_diagnostics_comparison_export_gui_contract.py
python .codex/scripts/deimos_diagnostics_comparison_export_gui_smoke.py
python .codex/scripts/deimos_phase66_diagnostics_comparison_export_gui_readiness.py
```

These checks confirm comparison export/save wording, default filename generation, safe bundle reporting, and the no-install/no-helper-launch safety contract.

### Phase 67 diagnostics comparison report import/review

```bash
python .codex/scripts/deimos_diagnostics_comparison_report_import.py path/to/comparison-report.zip
python .codex/scripts/deimos_phase67_diagnostics_report_import_readiness.py
```

The imported report must stay read-only and must reject any executable payloads.

### Phase 68 diagnostics report import GUI readiness

```bash
python .codex/scripts/deimos_phase68_diagnostics_report_import_gui_readiness.py
```
