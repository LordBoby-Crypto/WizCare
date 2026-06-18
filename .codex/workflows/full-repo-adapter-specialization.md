# Full repo adapter specialization

Use after copying the plugin repo-copy files into a full Deimos repo checkout.

```bash
python skills/deimos-wizard101-engineer/scripts/deimos_full_repo_adapter_report.py . .codex/reports/full-repo-adapter.json
python skills/deimos-wizard101-engineer/scripts/deimos_command_surface_report.py . .codex/reports/command-surface.json
python skills/deimos-wizard101-engineer/scripts/deimos_traversal_w101_link_report.py . .codex/reports/traversal-w101-links.json
python skills/deimos-wizard101-engineer/scripts/deimos_release_locale_full_repo_report.py . .codex/reports/release-locale.json
```

Before editing bot, combat, route, questing, sigil, or drop-logging code, read the generated reports and link any zone/boss/spell/drop assumptions to Wizard101 data records.
