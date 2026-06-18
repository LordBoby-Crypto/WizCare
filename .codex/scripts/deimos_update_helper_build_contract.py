#!/usr/bin/env python3
from __future__ import annotations
import ast, json, re, sys
from pathlib import Path


def main() -> int:
    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else repo/'.codex/reports/phase43-helper-build-contract.json'
    helper_dir = repo/'libs/updater_helper'
    source = helper_dir/'deimos_updater_helper.py'
    spec = helper_dir/'deimos_updater_helper.spec'
    build = helper_dir/'build_helper.py'
    blockers: list[str] = []
    warnings: list[str] = []
    for p in (source, spec, build):
        if not p.exists():
            blockers.append(f'missing {p.relative_to(repo)}')
    if spec.exists():
        text = spec.read_text(encoding='utf-8')
        required = ['deimos_updater_helper.py', 'deimos-updater-helper', 'console=True']
        for token in required:
            if token not in text:
                blockers.append(f'spec missing {token}')
        if 'update_check.py' in text or 'Deimos.py' in text:
            blockers.append('helper spec must not package the GUI or main app')
    if build.exists():
        try:
            ast.parse(build.read_text(encoding='utf-8'))
        except SyntaxError as exc:
            blockers.append(f'build_helper.py syntax error: {exc}')
    if source.exists():
        text = source.read_text(encoding='utf-8')
        if '--dry-run' not in text:
            blockers.append('helper scaffold must keep --dry-run requirement')
        if re.search(r'os\.replace|shutil\.move|subprocess\.Popen', text):
            blockers.append('helper scaffold must not replace files or relaunch processes yet')
    report = {'phase': 43, 'ok': not blockers, 'blockers': blockers, 'warnings': warnings}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(report, sort_keys=True))
    return 1 if blockers else 0

if __name__ == '__main__':
    raise SystemExit(main())
