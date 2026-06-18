# Phase 53 Helper Install Dry-Run Harness Integration

Phase 53 connects the dry-run-only updater helper scaffold to the fake install test harness. The purpose is to prove that helper manifest parsing, checksum validation, JSONL logging, and fake replacement/rollback scenarios can be tested through one repeatable pathway.

Locked behavior remains locked:
- no GUI helper launch
- no non-dry-run helper execution
- no real executable replacement
- no relaunch
- no automatic install

The core check is `deimos_helper_install_dryrun_integration.py`, which builds a temporary fake release/install filesystem and invokes `libs/updater_helper/deimos_updater_helper.py` with `--dry-run`, then runs `.codex/scripts/deimos_update_install_test_harness.py` against all fake scenarios.
