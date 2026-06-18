# Phase 47: Helper Artifact Post-Build Enforcement

Phase 47 makes helper artifact checks strict only after helper build steps in publishing workflows. Earlier phases allowed helper artifacts to be optional while scaffolding was being introduced. From this phase forward:

- Release/build/develop publishing workflows must treat a missing helper executable as a blocker after the helper build step.
- Release packages must include both the helper executable and its checksum if the helper build step is present.
- CI can continue to run preflight checks without requiring release artifact upload behavior.
- The update install path remains disabled. These checks only prepare artifacts for future reviewed installer work.

## Required invariant

The helper checksum file must use:

```text
<64-hex-sha256>  deimos-updater-helper.exe
```

## Codex guidance

When changing release workflows, Codex must run the Phase 47 readiness checker and must not weaken strict workflow behavior by adding silent helper-copy fallbacks.
