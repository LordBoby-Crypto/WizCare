#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, subprocess, sys, tempfile
from pathlib import Path

def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    helper = root/'libs/updater_helper/deimos_updater_helper.py'
    blockers=[]; warnings=[]; cases=[]
    if not helper.exists():
        blockers.append('helper scaffold missing')
    else:
        with tempfile.TemporaryDirectory() as td:
            t=Path(td); staged=t/'Deimos.exe'; staged.write_bytes(b'fake deimos exe for phase 42 smoke')
            digest=hashlib.sha256(staged.read_bytes()).hexdigest()
            checksum=t/'Deimos.exe.sha256'; checksum.write_text(f'{digest}  Deimos.exe\n', encoding='utf-8')
            manifest=t/'deimos-helper-manifest.json'
            manifest.write_text(json.dumps({'schema_version':'1','operation':'dry_run_replace_exe','current_exe':str(t/'install'/'Deimos.exe'),'staged_exe':str(staged),'checksum_file':str(checksum),'rollback_dir':str(t/'rollback')}), encoding='utf-8')
            log=t/'helper.log'
            ok=subprocess.run([sys.executable,str(helper),'--manifest',str(manifest),'--wait-pid','123','--log',str(log),'--dry-run'], cwd=str(root), text=True, capture_output=True)
            cases.append({'name':'valid_dry_run','returncode':ok.returncode,'stdout':ok.stdout.strip(),'stderr':ok.stderr.strip()})
            if ok.returncode != 0: blockers.append('valid dry-run helper smoke failed')
            bad=subprocess.run([sys.executable,str(helper),'--manifest',str(manifest),'--wait-pid','123','--log',str(log)], cwd=str(root), text=True, capture_output=True)
            cases.append({'name':'no_dry_run_blocked','returncode':bad.returncode,'stdout':bad.stdout.strip(),'stderr':bad.stderr.strip()})
            if bad.returncode == 0: blockers.append('helper allowed non-dry-run execution')
    result={'phase':42,'check':'update_helper_scaffold_smoke','passed':not blockers,'blockers':blockers,'warnings':warnings,'cases':cases}
    out=root/'.codex/reports/phase42-update-helper-scaffold-smoke.json'; out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 0 if not blockers else 1
if __name__ == '__main__': raise SystemExit(main())
