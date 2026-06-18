# Phase 52 - Updater Install Test Harness Design

Phase 52 adds a fake-filesystem test harness for future updater install work. It does not unlock or implement real update installation.

## Purpose

Use this phase before any future real updater install implementation to prove that the design can be simulated safely:

- verify staged executable checksum before replacement
- create a rollback copy before replacement
- simulate successful replacement in a temporary folder
- simulate checksum failure before replacement
- simulate replacement failure and rollback restoration
- validate helper-style exit-code meanings
- write helper-like JSONL logs

## Hard locks

The harness must never:

- touch the real `Deimos.exe`
- launch `deimos-updater-helper.exe`
- call `os.replace` against the real app path
- relaunch Deimos
- enable automatic installation
- mutate real user files outside a temporary fake filesystem

## Scripts

Run:

```bash
python .codex/scripts/deimos_update_install_test_harness.py .codex/reports/phase52-harness.json --scenario all
python .codex/scripts/deimos_phase52_install_harness_readiness.py . .codex/reports/phase52-readiness.json
```

A passing Phase 52 report still means install execution is locked. It only proves the future install design can be tested without touching real binaries.
