# Phase 57 staged update UX/report polish

Phase 57 adds a single display-focused summary layer for staged updates. The summary must be safe to show in the GUI and in Codex reports.

Required summary categories:

- checksum status
- manifest status
- helper dry-run log status
- install-lock status
- missing staged assets
- review-only blockers

Hard locks:

- no helper launch from the GUI
- no executable replacement
- no relaunch
- no automatic install
- no non-dry-run helper execution
