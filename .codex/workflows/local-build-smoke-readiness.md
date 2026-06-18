# Phase 32: local build smoke and dependency readiness

Use this workflow before asking Codex to run or change a Deimos build locally.

1. Run dependency readiness without installing anything:

```bash
python .codex/scripts/deimos_local_dependency_readiness.py . .codex/reports/phase32-local-dependency-readiness.json
```

2. Run import/compile smoke checks:

```bash
python .codex/scripts/deimos_import_smoke_report.py . .codex/reports/phase32-import-smoke-report.json
```

3. Run the aggregate pre-build report:

```bash
python .codex/scripts/deimos_local_prebuild_report.py . .codex/reports/phase32-local-prebuild-report.json
```

4. Only attempt the real build after blockers are cleared:

```bash
uv python install
uv sync --group dev
uv run --group dev pyinstaller --noconfirm --clean Deimos.spec
```

Rules:
- Do not treat Linux/macOS local smoke failures involving `pywin32` as Windows build failures.
- Do treat Python version mismatches, missing `uv`, missing workspace members, missing spec inputs, and patched module compile failures as blockers.
- Do not import PyQt-heavy GUI modules as a smoke test unless dependencies have been installed; prefer AST/py_compile checks first.
