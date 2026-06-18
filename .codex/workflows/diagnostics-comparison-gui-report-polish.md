# Diagnostics comparison GUI/report polish workflow

1. Export two staged-update diagnostics bundles.
2. Run the Phase 62 comparison review script.
3. Inspect the generated severity, headline, rows, and next steps.
4. Treat blocker severity as a hard stop for updater install work.
5. Keep install execution locked until a future unlock-gate phase explicitly authorizes it.
