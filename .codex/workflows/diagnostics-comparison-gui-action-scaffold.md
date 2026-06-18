# Diagnostics Comparison GUI Action Scaffold Workflow

1. Export two staged-update diagnostics bundles using the Phase 59 export workflow.
2. Open the GUI diagnostics comparison action.
3. Choose the earlier bundle, then the later bundle.
4. Review the Phase 62 before/after summary.
5. Treat blocker severity as a hard stop.

The action is read-only. Do not add installer launch, helper launch, executable replacement, or relaunch behavior to this workflow.

## Validation

```bash
python .codex/scripts/deimos_phase63_diagnostics_comparison_gui_action_readiness.py
```
