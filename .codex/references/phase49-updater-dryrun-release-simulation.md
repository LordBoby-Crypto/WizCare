# Phase 49 updater dry-run release simulation

Phase 49 proves that the update pipeline components agree without using a real release or replacing any executable.

## Guarantees

- Uses fake artifact bytes only.
- Generates real SHA-256 checksums for the fake artifacts.
- Generates a release manifest with helper metadata.
- Validates the manifest in strict post-build mode.
- Runs `libs/updater_helper/deimos_updater_helper.py` with `--dry-run`.
- Requires the staged GUI review checksum state to be `verified`.
- Keeps install execution, helper launch from GUI, relaunch, and executable replacement locked.

## Failure policy

Treat any simulation failure as a blocker before adding real install behavior.
