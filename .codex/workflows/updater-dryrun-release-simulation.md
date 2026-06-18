# Phase 49: Updater dry-run release simulation

Run a fake release artifact simulation that does not touch the real executable:

```bash
python .codex/scripts/deimos_phase49_release_simulation_readiness.py . .codex/reports/phase49-release-simulation-readiness.json
```

The simulation creates fake `Deimos.exe` and `deimos-updater-helper.exe` files in `.codex/reports/phase49-simulated-release`, writes checksums and `release-manifest.json`, validates strict post-build manifest rules, runs the helper scaffold in `--dry-run`, and builds staged-review metadata.

Install execution must remain locked. Any non-dry-run helper call or GUI helper launch is out of scope for this phase.
