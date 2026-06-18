# Staged Helper Dry-Run Log Generation

Use this workflow after a staged update download has produced `Deimos.exe` and `Deimos.exe.sha256`.

1. Verify the staged folder contains both required files.
2. Run:

```bash
python .codex/scripts/deimos_helper_dryrun_log_generator.py . <staging-folder> .codex/reports/phase55-helper-dryrun-log.json
```

3. Confirm the report passes and contains no blockers.
4. Open the Deimos update review UI and use the helper dry-run review button to inspect the generated JSONL log.

Do not implement helper launch, non-dry-run install, executable replacement, relaunch, or automatic install in this workflow.
