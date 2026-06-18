# Deimos Wizard101 Repo Guidance

Treat `main` as the baseline. Ignore prior `3.14.0-dev` work unless explicitly requested.

Before changing gameplay, bot, zone, enemy, quest, gear, farming, or strategy logic:

1. Query the Wizard101 data index if available.
2. Check source metadata and coverage status.
3. Avoid guessing about enemy schools, spells, cheats, drops, quest order, or gear stats.
4. Mark unverified game assumptions clearly in the change summary.

Before release or packaging changes:

1. Run locale checks.
2. Run version consistency checks.
3. Run release readiness checks.
4. Verify PyInstaller assets and helper binaries.

Do not add stealth, bypass, credential, anti-detection, or account-abuse logic.

## Phase 9 drop/gear guardrail
Do not use family-level drop or gear records as exact best-gear data. Require exact stats and strategy-reviewed records before ranking gear.


## Phase 18 spell/item-card rules
Use exact spell facts only when `data_quality.exact_spell_page_verified` is true. Never infer best spell, PvP meta, spellwrighting route, or bot rotation from a pet item-card link or spellement drop alone.

## Phase 21 spell strategy policy

When using Wizard101 spell data in Deimos work, treat exact spell records as lookup facts only unless a strategy-reviewed record unlocks the requested recommendation. Keep PvE, PvP, raid, boss-cheat, item-card, and spellwrighting contexts separate. Do not generate cast-order or bot-rotation logic from pip cost, damage, or item-card facts alone.


## Phase 26 parser-aware bot validation

Before editing bot scripts, DeimosLang parser behavior, raw command parsing, combat configs, or route/pathing code, run the parser-aware validation workflow in `.codex/workflows/parser-aware-bot-validation.md`. Do not treat traversalData files as bot scripts. Parser-valid does not mean game-safe; still check Wizard101 entity/strategy maturity.


## Phase 27 GUI bot validation

When editing the bot editor or run button flow, use `.codex/workflows/gui-bot-validator-integration.md`. Validate bot text before queuing `GUICommandType.ExecuteBot`, keep warnings separate from blocking parser errors, and update `locale/en.lang` and `locale/zh.lang` together for all new GUI strings.


## Phase 31 build artifact rule

For CI, release, and packaging work, prefer `Deimos.spec` over raw PyInstaller commands. Run `.codex/scripts/deimos_pyinstaller_build_readiness.py` before release changes and treat missing locale/logo/manifest/version files or version mismatches as blockers.

## Phase 33 Windows build/release checks

Before Windows build or release work, run `.codex/scripts/deimos_windows_release_smoke.py`. After a real build, run `.codex/scripts/deimos_release_artifact_report.py --require-artifact` and do not claim release readiness if it reports blockers.



## Phase 36 update-system scaffold

Do not enable automatic self-update behavior without running `.codex/scripts/deimos_update_system_readiness.py`. Stable release assets are `Deimos.exe`, `Deimos.exe.sha256`, and `release-manifest.json`. The current scaffold may stage and verify assets only; executable replacement/relaunch remains locked.

## Phase 40 updater install-design review

Updater installation remains disabled. Codex must not add executable replacement, relaunch, or silent install behavior inside the GUI process. Use `.codex/workflows/updater-install-design-review.md` and run `.codex/scripts/deimos_phase40_install_design_readiness.py` before changing updater install code.


## Phase 41 updater helper specification

Before adding updater install behavior, run `.codex/scripts/deimos_phase41_update_helper_readiness.py`. Do not launch a helper or replace executables unless the user explicitly moves the project into an implementation phase.


## Phase 42 updater helper scaffold

Updater-helper work must remain dry-run only unless a later phase explicitly unlocks installation. Run `.codex/scripts/deimos_phase42_update_helper_readiness.py` before editing helper code.

## Phase 43 helper build packaging

Before changing updater-helper packaging, run `.codex/scripts/deimos_phase43_update_helper_build_readiness.py`. Do not wire the helper into the GUI or enable executable replacement.

## Phase 44 updater helper artifact validation
- Treat `deimos-updater-helper.exe` as the stable future helper artifact name.
- Use `.codex/scripts/deimos_phase44_helper_artifact_readiness.py` before packaging helper releases.
- Do not launch the helper from the GUI and do not replace `Deimos.exe` in this phase.

## PHASE45_HELPER_MANIFEST_INTEGRATION
Before release publishing, verify helper metadata with `.codex/scripts/deimos_phase45_helper_manifest_readiness.py`. Helper artifacts may be recorded in `release-manifest.json`, but helper launch, executable replacement, relaunch, and install execution remain locked.


## Phase 46 helper workflow rule
When editing GitHub Actions, preserve helper artifact build/check/upload steps and keep install execution locked. Run `.codex/scripts/deimos_phase46_helper_workflow_readiness.py` before release changes.

## Phase 47: helper artifact post-build enforcement

Publishing workflows (`build.yml`, `develop.yml`, `release.yml`) must fail if `deimos-updater-helper.exe` or `deimos-updater-helper.exe.sha256` is missing after the helper build step. CI may remain preflight-oriented. Do not enable GUI helper launch, executable replacement, relaunch, or automatic installation.


## Phase 48 helper manifest validation

For release work, run `.codex/scripts/deimos_phase48_manifest_postbuild_readiness.py`. Use `--strict-postbuild` only after Windows build artifacts exist. Keep updater helper launch and install execution locked.

## Phase 49 updater simulation rule

Before enabling any updater install behavior, run the Phase 49 dry-run release simulation and confirm it passes. Install execution, helper launch, executable replacement, and relaunch remain locked.


## Phase 50 update install unlock gate

Keep update installation locked. Run `.codex/scripts/deimos_phase50_install_unlock_readiness.py` before any future install implementation work. Do not launch updater helpers or replace executables in this phase.

## Phase 52 updater install test harness

Before any updater install implementation, run `.codex/scripts/deimos_phase52_install_harness_readiness.py`. The harness is simulation-only; do not enable helper launch, executable replacement, relaunch, or automatic installation.


## Phase 53 updater-helper dry-run harness rule
Before changing updater helper/install behavior, run `.codex/scripts/deimos_phase53_helper_install_dryrun_readiness.py`. Keep GUI helper launch, real executable replacement, relaunch, automatic install, and non-dry-run helper behavior disabled unless a later explicit unlock phase changes this rule.


## Phase 55 update safety

Use `.codex/scripts/deimos_helper_dryrun_log_generator.py` to generate helper dry-run JSONL logs from staged update files. Keep GUI helper launch and real install behavior locked.

## Phase 58 - staged update problem-resolution guidance
Adds display/report guidance for staged update issue states: missing assets, checksum mismatch, invalid manifest, missing/incomplete helper dry-run logs, and install-lock status. Install execution remains locked.

## Phase 59 staged update diagnostics export
Use the diagnostics export workflow for staged update support/debug bundles. Do not include executable payloads in exported diagnostics. Install and helper launch remain locked.


## Phase 61 - Diagnostics comparison report

Use the Phase 61 diagnostics comparison scripts to compare two staged-update diagnostics bundles in read-only mode. Bundles containing executable payloads must be rejected. Any lock-state change that enables install execution, GUI helper launch, non-dry-run behavior, or real replacement is a blocker.


## Phase 62 - diagnostics comparison GUI/report polish

Use `.codex/scripts/deimos_staged_update_diagnostics_comparison_review.py` to produce user-facing before/after diagnostics summaries. This is read-only and must not enable helper launch, executable replacement, or non-dry-run install behavior.


## Phase 63 - diagnostics comparison GUI action scaffold

The diagnostics comparison GUI action must stay read-only. It may open two exported diagnostics ZIPs and display the Phase 62 comparison review, but it must not import executable payloads, launch updater helpers, replace executables, relaunch Deimos, or enable install execution. Run `.codex/scripts/deimos_phase63_diagnostics_comparison_gui_action_readiness.py` after changes.

## Phase 64 guardrail - diagnostics comparison GUI wiring

The `Compare diagnostics` GUI button is review-only. It may read exported staged-update diagnostics bundles and show a comparison summary, but it must not import executable payloads, launch helpers, replace `Deimos.exe`, relaunch Deimos, or enable install execution.

Before changing this flow, run:

```bash
python .codex/scripts/deimos_phase64_diagnostics_comparison_gui_wiring_readiness.py
```

## Phase 65 - Diagnostics Comparison Export/Share Polish

Phase 65 adds safe export/share support for diagnostics comparison results. The export bundle contains comparison review metadata, the lower-level comparison report, source summaries, and a README. It must exclude `Deimos.exe`, updater helper executables, and all executable payloads. The diagnostics comparison export is read-only and does not enable helper launch, install execution, non-dry-run behavior, executable replacement, or Deimos relaunch.

Primary validation:

```bash
python .codex/scripts/deimos_phase65_diagnostics_comparison_export_readiness.py
```


## Phase 66 - Diagnostics Comparison Export GUI Polish

Phase 66 improves diagnostics comparison export/save UX with safer default filenames, clearer success/failure summaries, and explicit executable-exclusion wording. The export flow remains read-only and must not import executables, launch helpers, replace `Deimos.exe`, relaunch Deimos, or enable install execution.

Primary validation:

```bash
python .codex/scripts/deimos_phase66_diagnostics_comparison_export_gui_readiness.py
```

## Phase 67 - Diagnostics comparison exported-report import/review

- Added safe import/review for diagnostics-comparison report bundles exported by the Phase 65/66 comparison export flow.
- The import review rejects executable payloads and summarizes safe report metadata for support/debug review.
- Keep this path read-only: no helper launch, no executable import, no install execution, no non-dry-run behavior, and no real install attempt.
- Run `python .codex/scripts/deimos_phase67_diagnostics_report_import_readiness.py` before changing comparison report import/review behavior.

## Phase 68 - Diagnostics report import GUI polish

- Adds a safe GUI import/review action for exported diagnostics comparison report bundles.
- The import path rejects executable payloads and malformed report bundles.
- This remains support/debug-only: no helper launch, no executable replacement, no relaunch, and no install execution.
