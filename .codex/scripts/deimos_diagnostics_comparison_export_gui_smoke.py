#!/usr/bin/env python3
from __future__ import annotations
import json, sys, zipfile, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.update_system import build_diagnostics_comparison_export_gui_summary, export_diagnostics_comparison_report_bundle, diagnostics_comparison_export_default_filename


def make_diag(path: Path, checksum: str, log_status: str) -> None:
    data = {
        "review_only": True,
        "safe_bundle": True,
        "staged_asset_review": {"checksum_status": checksum, "manifest": {"status": "present"}},
        "helper_dry_run_review": {"helper_log_status": log_status},
        "problem_resolution_guidance": {"problems": []},
        "install_lock_state": {"install_locked": True, "install_execution_enabled": False, "helper_launch_from_gui_enabled": False, "non_dry_run_enabled": False, "real_install_attempted": False},
    }
    with zipfile.ZipFile(path, 'w') as zf:
        zf.writestr('deimos-staged-update-diagnostics.json', json.dumps(data))
        zf.writestr('README.txt', 'safe staged update diagnostics')


def main() -> int:
    blockers = []
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        before = td/'before.zip'; after = td/'after.zip'
        make_diag(before, 'verified', 'missing')
        make_diag(after, 'verified', 'valid')
        name = diagnostics_comparison_export_default_filename({"severity":"info", "difference_count":1})
        out = td/name
        export = export_diagnostics_comparison_report_bundle(before, after, out)
        summary = build_diagnostics_comparison_export_gui_summary(export.get('comparison_review'), export, out)
        if not out.exists(): blockers.append('comparison export zip was not written')
        if summary.get('status') != 'saved': blockers.append('GUI summary did not report saved')
        if summary.get('safe_bundle') is not True: blockers.append('GUI summary did not preserve safe_bundle=true')
        with zipfile.ZipFile(out) as zf:
            names = zf.namelist()
            if any(Path(n).suffix.lower() in {'.exe','.dll','.msi','.bat','.cmd','.ps1'} for n in names):
                blockers.append('export bundle contains executable-like payload')
    report = {"phase":66,"smoke":"diagnostics-comparison-export-gui","passed":not blockers,"blockers":blockers}
    out_report = ROOT/'.codex/reports/phase66-diagnostics-comparison-export-gui-smoke.json'
    out_report.parent.mkdir(parents=True, exist_ok=True)
    out_report.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not blockers else 1
if __name__ == '__main__':
    raise SystemExit(main())
