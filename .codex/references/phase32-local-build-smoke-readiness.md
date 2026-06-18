# Phase 32 - Local Build Smoke and Dependency Readiness

Phase 32 adds local pre-build safety checks for the patched Deimos main repo.

## Purpose

Before Codex attempts a local build, it must distinguish between:

- repo blockers, such as missing build inputs, mismatched Python requirement, or broken patched modules;
- environment gaps, such as `uv`, PyInstaller, PyQt6, or Windows-only pywin32 modules not being installed yet;
- expected platform limitations, such as checking a Windows app from Linux.

## Required checks

Run:

```bash
python .codex/scripts/deimos_local_prebuild_report.py . .codex/reports/phase32-local-prebuild-report.json
```

The aggregate report calls:

- `deimos_local_dependency_readiness.py`
- `deimos_import_smoke_report.py`

## Interpretation

A local machine is build-ready only when the aggregate report has `local_machine_build_ready: true`.

If the report blocks because the current Python is below the project requirement, use the repo's normal uv flow:

```bash
uv python install
uv sync --group dev
```

If PyQt6 or PyInstaller is not importable before dependency installation, treat that as an environment warning rather than a code defect.

## Safety

Do not use the smoke report to change runtime behavior. It is a no-mutation diagnostic layer for Codex and maintainers.
