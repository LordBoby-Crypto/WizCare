#!/usr/bin/env python3
from __future__ import annotations
import json, sys, zipfile, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.update_system import (
    STAGED_DIAGNOSTICS_FILENAME,
    compare_staged_update_diagnostics_bundles,
    build_diagnostics_comparison_review,
    compare_staged_update_diagnostics_bundles_for_review,
)

def write_bundle(path: Path, checksum="verified", manifest="valid", helper="valid", blockers=0, install_execution=False):
    diag = {
        "review_only": True,
        "install_locked": True,
        "install_execution_enabled": install_execution,
        "helper_launch_from_gui_enabled": False,
        "non_dry_run_enabled": False,
        "real_install_attempted": False,
        "summary": {
            "headline": "test bundle",
            "checksum_status": checksum,
            "manifest_status": manifest,
            "helper_log_status": helper,
            "problem_count": blockers,
            "blocker_count": blockers,
            "warning_count": 0,
            "install_locked": True,
            "install_execution_enabled": install_execution,
            "helper_launch_from_gui_enabled": False,
            "non_dry_run_enabled": False,
            "real_install_attempted": False,
        },
    }
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(STAGED_DIAGNOSTICS_FILENAME, json.dumps(diag))
        zf.writestr("README.txt", "safe diagnostics")
        zf.writestr("artifacts/Deimos.exe.sha256", "abc  Deimos.exe\n")

def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        a = td/'before.zip'; b = td/'after.zip'; unsafe = td/'unsafe.zip'
        write_bundle(a)
        write_bundle(b, checksum='mismatch', helper='incomplete', blockers=1)
        write_bundle(unsafe, install_execution=True)
        comparison = compare_staged_update_diagnostics_bundles(a, b)
        review = build_diagnostics_comparison_review(comparison)
        full = compare_staged_update_diagnostics_bundles_for_review(a, b)
        unsafe_review = compare_staged_update_diagnostics_bundles_for_review(a, unsafe)
        checks = {
            'review_valid': review.get('valid') is True,
            'review_warning_severity': review.get('severity') == 'warning',
            'review_has_rows': len(review.get('rows', [])) >= 2,
            'review_has_next_steps': bool(review.get('next_steps')),
            'full_embeds_comparison': isinstance(full.get('comparison'), dict),
            'full_read_only': full.get('install_execution_enabled') is False and full.get('real_install_attempted') is False,
            'unsafe_lock_blocker': unsafe_review.get('severity') == 'blocker' or unsafe_review.get('valid') is False,
        }
    out = {'passed': all(checks.values()), 'checks': checks}
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if out['passed'] else 1
if __name__ == '__main__':
    raise SystemExit(main())
