#!/usr/bin/env python3
"""Enforce helper artifact requirements after release/build helper build steps.

This checker is strict for publishing workflows and permissive for CI/preflight.
It does not launch installers or perform update installation.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

HELPER = Path('libs/updater_helper/dist/deimos-updater-helper.exe')
HELPER_SHA = Path('libs/updater_helper/dist/deimos-updater-helper.exe.sha256')
STRICT_WORKFLOWS = [
    Path('.github/workflows/build.yml'),
    Path('.github/workflows/release.yml'),
    Path('.github/workflows/develop.yml'),
]
CI_WORKFLOW = Path('.github/workflows/ci.yml')


def workflow_text(repo: Path, wf: Path) -> str:
    path = repo / wf
    return path.read_text(encoding='utf-8') if path.exists() else ''


def analyze_workflow(repo: Path, wf: Path, strict: bool) -> dict:
    text = workflow_text(repo, wf)
    blockers: list[str] = []
    warnings: list[str] = []
    if not text:
        blockers.append(f'{wf} is missing')
        return {'workflow': str(wf), 'strict': strict, 'blockers': blockers, 'warnings': warnings, 'passed': False}

    has_build = 'deimos_updater_helper.spec' in text
    has_checksum_write = 'deimos_update_helper_artifact_report.py' in text and '--write-checksum' in text
    has_require = 'deimos_update_helper_artifact_report.py' in text and '--require-artifact' in text
    copies_helper = 'deimos-updater-helper.exe' in text
    copies_helper_sha = 'deimos-updater-helper.exe.sha256' in text
    has_silently_continue = re.search(r'deimos-updater-helper\.exe[^\n]*ErrorAction\s+SilentlyContinue', text, re.I) is not None or re.search(r'deimos-updater-helper\.exe\.sha256[^\n]*ErrorAction\s+SilentlyContinue', text, re.I) is not None
    has_manifest_inclusion = 'deimos_release_manifest_helper_integration.py' in text or 'deimos_helper_release_asset_matrix.py' in text

    if not has_build:
        blockers.append('helper build step is missing')
    if not has_checksum_write:
        blockers.append('helper checksum generation step is missing')
    if strict:
        if not has_require:
            blockers.append('strict workflow must require the helper artifact after building it')
        if not copies_helper or not copies_helper_sha:
            blockers.append('strict workflow must package helper executable and checksum')
        if has_silently_continue:
            blockers.append('strict workflow must not silently ignore missing helper artifacts')
        if not has_manifest_inclusion:
            warnings.append('strict workflow does not explicitly run helper manifest-inclusion audit')
    else:
        if has_silently_continue:
            warnings.append('CI/preflight may tolerate missing helper artifacts, but keep publishing workflows strict')

    return {
        'workflow': str(wf),
        'strict': strict,
        'has_build_step': has_build,
        'has_checksum_generation': has_checksum_write,
        'requires_artifact': has_require,
        'copies_helper': copies_helper,
        'copies_helper_checksum': copies_helper_sha,
        'uses_erroraction_silentlycontinue_for_helper': has_silently_continue,
        'has_manifest_inclusion_audit': has_manifest_inclusion,
        'blockers': blockers,
        'warnings': warnings,
        'passed': not blockers,
    }


def analyze(repo: Path) -> dict:
    workflows = [analyze_workflow(repo, wf, True) for wf in STRICT_WORKFLOWS]
    workflows.append(analyze_workflow(repo, CI_WORKFLOW, False))
    blockers = [f"{w['workflow']}: {b}" for w in workflows for b in w['blockers']]
    warnings = [f"{w['workflow']}: {x}" for w in workflows for x in w['warnings']]
    return {
        'phase': 47,
        'purpose': 'helper artifact post-build enforcement',
        'strict_workflows': [str(w) for w in STRICT_WORKFLOWS],
        'preflight_workflows': [str(CI_WORKFLOW)],
        'helper_artifact': str(HELPER),
        'helper_checksum': str(HELPER_SHA),
        'install_execution_locked': True,
        'workflows': workflows,
        'blockers': blockers,
        'warnings': warnings,
        'passed': not blockers,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument('repo', nargs='?', default='.')
    p.add_argument('output', nargs='?', default='.codex/reports/phase47-helper-postbuild-enforcement.json')
    a = p.parse_args(argv)
    repo = Path(a.repo).resolve()
    result = analyze(repo)
    out = repo / a.output if not Path(a.output).is_absolute() else Path(a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(result, sort_keys=True))
    return 0 if result['passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
