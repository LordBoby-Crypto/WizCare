#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.update_system import build_staged_update_problem_resolution_guidance, ReleaseInfo, ReleaseAsset, STABLE_EXE_ASSET, STABLE_CHECKSUM_ASSET, STABLE_MANIFEST_ASSET


def fake_release() -> ReleaseInfo:
    assets = {
        STABLE_EXE_ASSET: ReleaseAsset(STABLE_EXE_ASSET, 'https://example.invalid/Deimos.exe', 11, 'application/octet-stream'),
        STABLE_CHECKSUM_ASSET: ReleaseAsset(STABLE_CHECKSUM_ASSET, 'https://example.invalid/Deimos.exe.sha256', 80, 'text/plain'),
        STABLE_MANIFEST_ASSET: ReleaseAsset(STABLE_MANIFEST_ASSET, 'https://example.invalid/release-manifest.json', 120, 'application/json'),
    }
    return ReleaseInfo('v3.13.1', 'fake', 'https://example.invalid/releases/v3.13.1', False, False, assets, {})


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT/'.codex/reports/phase58-resolution-contract.json'
    report = {'ok': True, 'blockers': []}
    try:
        guidance = build_staged_update_problem_resolution_guidance(fake_release(), {})
        required = {'review_only','version','headline','problem_count','blocker_count','warning_count','info_count','problems','checksum_status','manifest_status','helper_log_status','install_locked','summary'}
        missing = sorted(required - set(guidance))
        if missing:
            report['ok'] = False; report['blockers'].append('missing guidance keys: '+', '.join(missing))
        codes = {p.get('code') for p in guidance.get('problems', [])}
        for code in ('missing_staged_executable','missing_checksum_file','missing_release_manifest','missing_helper_dry_run_log','install_locked_by_design'):
            if code not in codes:
                report['ok'] = False; report['blockers'].append('missing problem code: '+code)
        if not guidance.get('install_locked'):
            report['ok'] = False; report['blockers'].append('install lock not reported')
        report['guidance'] = guidance
    except Exception as exc:
        report['ok'] = False; report['blockers'].append(str(exc))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report['ok'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
