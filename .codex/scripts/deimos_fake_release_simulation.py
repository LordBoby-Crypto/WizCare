#!/usr/bin/env python3
"""Phase 49: simulate a complete updater release artifact set without touching the real executable.

This script creates a fake release set in a simulation folder, generates checksums and a
release manifest, validates the post-build manifest contract, runs the dry-run-only
updater helper scaffold, and builds the same staged review metadata used by the GUI.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, subprocess, sys, tempfile
from pathlib import Path

PRIMARY_EXE='Deimos.exe'
PRIMARY_SHA='Deimos.exe.sha256'
MANIFEST='release-manifest.json'
HELPER_EXE='deimos-updater-helper.exe'
HELPER_SHA='deimos-updater-helper.exe.sha256'


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load_update_system(repo: Path):
    p=repo/'src/update_system.py'
    spec=importlib.util.spec_from_file_location('deimos_update_system_phase49', p)
    mod=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def write_fake_artifacts(repo: Path, sim_dir: Path) -> dict[str, Path]:
    dist=sim_dir/'dist'
    helper_dist=sim_dir/'libs/updater_helper/dist'
    dist.mkdir(parents=True, exist_ok=True)
    helper_dist.mkdir(parents=True, exist_ok=True)
    exe=dist/PRIMARY_EXE
    helper=helper_dist/HELPER_EXE
    # intentionally not valid executables; this is a contract/checksum simulation only.
    exe.write_bytes(b'DEIMOS_PHASE49_FAKE_EXECUTABLE\n' + b'A'*4096)
    helper.write_bytes(b'DEIMOS_PHASE49_FAKE_HELPER\n' + b'B'*2048)
    (dist/PRIMARY_SHA).write_text(f'{sha256(exe)}  {PRIMARY_EXE}\n', encoding='utf-8')
    (helper_dist/HELPER_SHA).write_text(f'{sha256(helper)}  {HELPER_EXE}\n', encoding='utf-8')
    return {'repo':sim_dir,'dist':dist,'helper_dist':helper_dist,'exe':exe,'helper':helper}


def copy_release_scripts(repo: Path, sim_repo: Path) -> None:
    # Copy the same .codex scripts needed by the release checks into the isolated simulation repo.
    src_scripts=repo/'.codex/scripts'
    dst_scripts=sim_repo/'.codex/scripts'
    dst_scripts.mkdir(parents=True, exist_ok=True)
    needed=[
        'deimos_checksum_release_artifacts.py',
        'deimos_release_manifest_postbuild_validation.py',
        'deimos_release_manifest_helper_integration.py',
        'deimos_update_helper_scaffold_contract.py',
    ]
    for name in needed:
        src=src_scripts/name
        if src.exists():
            shutil.copy2(src, dst_scripts/name)
    src_update=repo/'src/update_system.py'
    (sim_repo/'src').mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_update, sim_repo/'src/update_system.py')
    # version source for manifest generation
    deimos=repo/'Deimos.py'
    if deimos.exists():
        shutil.copy2(deimos, sim_repo/'Deimos.py')


def main(argv=None) -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('repo', nargs='?', default='.')
    ap.add_argument('output', nargs='?', default='.codex/reports/phase49-dryrun-release-simulation.json')
    ap.add_argument('--simulation-dir', default=None, help='optional directory for generated fake release artifacts')
    args=ap.parse_args(argv)
    repo=Path(args.repo).resolve()
    out=Path(args.output)
    sim_root=Path(args.simulation_dir).resolve() if args.simulation_dir else repo/'.codex/reports/phase49-simulated-release'
    if sim_root.exists():
        shutil.rmtree(sim_root)
    sim_root.mkdir(parents=True, exist_ok=True)
    blockers=[]; warnings=[]; checks=[]
    try:
        paths=write_fake_artifacts(repo, sim_root)
        copy_release_scripts(repo, sim_root)
        # Generate manifest in the simulation repo using the actual release checksum script.
        cmd=[sys.executable, str(sim_root/'.codex/scripts/deimos_checksum_release_artifacts.py'), str(sim_root), str(sim_root/'.codex/reports/checksum.json'), '--write', '--require-artifact', '--require-helper-artifact']
        proc=subprocess.run(cmd, text=True, capture_output=True)
        checks.append({'name':'checksum_manifest_generation','cmd':cmd,'returncode':proc.returncode,'stdout':proc.stdout[-4000:],'stderr':proc.stderr[-4000:]})
        if proc.returncode:
            blockers.append('fake release checksum/manifest generation failed')
        # Strict post-build manifest validation should pass against the fake artifact set.
        cmd=[sys.executable, str(repo/'.codex/scripts/deimos_release_manifest_postbuild_validation.py'), str(sim_root), str(sim_root/'.codex/reports/postbuild-validation.json'), '--require-manifest', '--require-artifacts', '--require-helper']
        proc=subprocess.run(cmd, text=True, capture_output=True)
        checks.append({'name':'strict_postbuild_manifest_validation','cmd':cmd,'returncode':proc.returncode,'stdout':proc.stdout[-4000:],'stderr':proc.stderr[-4000:]})
        if proc.returncode:
            blockers.append('strict post-build manifest validation failed on fake release set')
        # Build GUI staged-review metadata from the same fake files.
        mod=load_update_system(repo)
        release=mod.ReleaseInfo(
            tag_name='v9.99.49-simulated', name='Phase 49 Simulated Release', html_url='https://example.invalid/deimos/phase49', prerelease=False, draft=False,
            assets={
                PRIMARY_EXE: mod.ReleaseAsset(PRIMARY_EXE, 'file://'+str(paths['exe']), paths['exe'].stat().st_size),
                PRIMARY_SHA: mod.ReleaseAsset(PRIMARY_SHA, 'file://'+str(paths['dist']/PRIMARY_SHA), (paths['dist']/PRIMARY_SHA).stat().st_size),
                MANIFEST: mod.ReleaseAsset(MANIFEST, 'file://'+str(paths['dist']/MANIFEST), (paths['dist']/MANIFEST).stat().st_size),
            }, raw={'simulation': True}
        )
        staged={PRIMARY_EXE: paths['exe'], PRIMARY_SHA: paths['dist']/PRIMARY_SHA, MANIFEST: paths['dist']/MANIFEST}
        review=mod.build_staged_asset_review(release, staged)
        if review.get('checksum_status') != 'verified':
            blockers.append('staged review did not verify fake Deimos.exe checksum')
        helper_manifest={
            'schema_version':'1.0',
            'operation':'dry_run_replace_exe',
            'current_exe':str(sim_root/'installed/Deimos.exe'),
            'staged_exe':str(paths['exe']),
            'checksum_file':str(paths['dist']/PRIMARY_SHA),
            'rollback_dir':str(sim_root/'rollback'),
        }
        helper_manifest_path=sim_root/'deimos-helper-manifest.json'
        helper_manifest_path.write_text(json.dumps(helper_manifest, indent=2), encoding='utf-8')
        helper_log=sim_root/'deimos-updater-helper.log'
        helper_py=repo/'libs/updater_helper/deimos_updater_helper.py'
        cmd=[sys.executable, str(helper_py), '--manifest', str(helper_manifest_path), '--wait-pid', '1234', '--log', str(helper_log), '--dry-run']
        proc=subprocess.run(cmd, text=True, capture_output=True)
        checks.append({'name':'helper_dry_run','cmd':cmd,'returncode':proc.returncode,'stdout':proc.stdout[-4000:],'stderr':proc.stderr[-4000:]})
        if proc.returncode:
            blockers.append('dry-run helper failed on fake release set')
        helper_log_events=[]
        if helper_log.exists():
            helper_log_events=[json.loads(line) for line in helper_log.read_text(encoding='utf-8').splitlines() if line.strip()]
        if not any(e.get('event')=='dry_run_complete' for e in helper_log_events):
            blockers.append('helper dry-run log did not contain dry_run_complete')
        manifest=json.loads((paths['dist']/MANIFEST).read_text(encoding='utf-8')) if (paths['dist']/MANIFEST).exists() else {}
        artifact_names=[a.get('name') for a in manifest.get('artifacts', [])]
        for required in (PRIMARY_EXE, PRIMARY_SHA, MANIFEST, HELPER_EXE, HELPER_SHA):
            if required not in artifact_names:
                blockers.append(f'simulated manifest missing artifact metadata: {required}')
        report={
            'phase':49,
            'simulation_dir':str(sim_root),
            'install_execution_locked':True,
            'real_executable_touched':False,
            'fake_artifacts_only':True,
            'checks':checks,
            'staged_review_checksum_status':review.get('checksum_status'),
            'staged_review_install_locked':review.get('install_locked'),
            'helper_log_events':helper_log_events,
            'manifest_artifacts':artifact_names,
            'blockers':blockers,
            'warnings':warnings,
            'passed':not blockers,
        }
    except Exception as exc:
        report={'phase':49,'simulation_dir':str(sim_root),'blockers':[f'unexpected simulation error: {exc}'],'warnings':warnings,'passed':False}
    out = out if out.is_absolute() else repo/out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(report, sort_keys=True))
    return 0 if report.get('passed') else 1

if __name__=='__main__':
    # local import needed only inside copy_release_scripts
    import shutil
    raise SystemExit(main())
