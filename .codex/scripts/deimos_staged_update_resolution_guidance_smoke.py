#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.update_system import build_staged_update_problem_resolution_guidance, ReleaseInfo, ReleaseAsset, STABLE_EXE_ASSET, STABLE_CHECKSUM_ASSET, STABLE_MANIFEST_ASSET, HELPER_LOG_NAME


def fake_release() -> ReleaseInfo:
    assets = {
        STABLE_EXE_ASSET: ReleaseAsset(STABLE_EXE_ASSET, 'https://example.invalid/Deimos.exe', 11, 'application/octet-stream'),
        STABLE_CHECKSUM_ASSET: ReleaseAsset(STABLE_CHECKSUM_ASSET, 'https://example.invalid/Deimos.exe.sha256', 80, 'text/plain'),
        STABLE_MANIFEST_ASSET: ReleaseAsset(STABLE_MANIFEST_ASSET, 'https://example.invalid/release-manifest.json', 120, 'application/json'),
    }
    return ReleaseInfo('v3.13.1', 'fake', 'https://example.invalid/releases/v3.13.1', False, False, assets, {})


def make_stage(kind: str) -> dict[str, Path]:
    d = Path(tempfile.mkdtemp(prefix='deimos-phase58-'))
    exe = d/STABLE_EXE_ASSET
    exe.write_bytes(b'fake deimos exe')
    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    checksum = d/STABLE_CHECKSUM_ASSET
    checksum.write_text(f'{digest}  Deimos.exe\n', encoding='utf-8')
    manifest = d/STABLE_MANIFEST_ASSET
    manifest.write_text(json.dumps({'version':'3.13.1','artifacts':[]}), encoding='utf-8')
    if kind == 'checksum_mismatch':
        checksum.write_text('0'*64 + '  Deimos.exe\n', encoding='utf-8')
    elif kind == 'invalid_manifest':
        manifest.write_text('{not-json', encoding='utf-8')
    elif kind == 'valid_log':
        (d/HELPER_LOG_NAME).write_text('\n'.join(json.dumps({'event': e}) for e in ['manifest_loaded','checksum_verified','dry_run_complete'])+'\n', encoding='utf-8')
    elif kind == 'incomplete_log':
        (d/HELPER_LOG_NAME).write_text(json.dumps({'event':'plan_built'})+'\n', encoding='utf-8')
    elif kind == 'invalid_log':
        (d/HELPER_LOG_NAME).write_text('not-json\n', encoding='utf-8')
    return {STABLE_EXE_ASSET: exe, STABLE_CHECKSUM_ASSET: checksum, STABLE_MANIFEST_ASSET: manifest}


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT/'.codex/reports/phase58-resolution-smoke.json'
    cases = {}
    ok = True
    for kind in ['missing_all','checksum_mismatch','invalid_manifest','missing_log','incomplete_log','invalid_log','valid_log']:
        paths = {} if kind == 'missing_all' else make_stage(kind)
        guidance = build_staged_update_problem_resolution_guidance(fake_release(), paths)
        codes = [p.get('code') for p in guidance.get('problems', [])]
        cases[kind] = {'headline': guidance.get('headline'), 'codes': codes, 'blockers': guidance.get('blocker_count'), 'warnings': guidance.get('warning_count')}
    expectations = {
        'missing_all': 'missing_staged_executable',
        'checksum_mismatch': 'checksum_mismatch',
        'invalid_manifest': 'invalid_release_manifest',
        'missing_log': 'missing_helper_dry_run_log',
        'incomplete_log': 'incomplete_helper_dry_run_log',
        'invalid_log': 'invalid_helper_dry_run_log',
        'valid_log': 'install_locked_by_design',
    }
    blockers = []
    for case, code in expectations.items():
        if code not in cases[case]['codes']:
            ok = False; blockers.append(f'{case} did not include {code}')
    report = {'ok': ok, 'blockers': blockers, 'cases': cases}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 1

if __name__ == '__main__':
    raise SystemExit(main())
