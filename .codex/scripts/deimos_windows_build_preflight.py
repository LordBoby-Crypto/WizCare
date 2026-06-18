#!/usr/bin/env python3
"""Windows-specific Deimos build preflight.
Checks expected commands/files before running a Windows PyInstaller release build.
Does not build or mutate the repo.
"""
from __future__ import annotations
import json, os, platform, re, shutil, sys
from pathlib import Path


def read(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8', errors='ignore')
    except FileNotFoundError:
        return ''


def pyproject_dev_deps(text: str) -> list[str]:
    # simple, dependency-light extraction for [dependency-groups] dev = [...] style
    deps = []
    m = re.search(r'(?ms)^dev\s*=\s*\[(.*?)\]', text)
    if m:
        for q in re.findall(r'["\']([^"\']+)["\']', m.group(1)):
            deps.append(q)
    return deps


def main() -> int:
    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    blockers, warnings = [], []
    files = {
        'Deimos.py': repo/'Deimos.py',
        'Deimos.spec': repo/'Deimos.spec',
        'pyproject.toml': repo/'pyproject.toml',
        'version_info.txt': repo/'version_info.txt',
        'app.manifest': repo/'app.manifest',
        'Deimos-logo.ico': repo/'Deimos-logo.ico',
    }
    for name, path in files.items():
        if not path.exists():
            blockers.append(f'missing required build input: {name}')
    if not (repo/'uv.lock').exists():
        warnings.append('uv.lock is missing; dependency resolution may be less reproducible')
    pp = read(files['pyproject.toml'])
    deps = pyproject_dev_deps(pp)
    dep_join = '\n'.join(deps).lower()
    for need in ['pyinstaller']:
        if need not in dep_join and need not in pp.lower():
            warnings.append(f'could not find {need} in pyproject dev dependencies')
    spec = read(files['Deimos.spec'])
    for token in ['locale', 'app.manifest', 'version_info.txt', 'Deimos-logo.ico']:
        if token not in spec:
            blockers.append(f'Deimos.spec does not mention {token}')
    if 'collect_submodules' not in spec and 'hiddenimports' not in spec:
        warnings.append('Deimos.spec may not declare hidden imports/collect_submodules')
    workflows = sorted((repo/'.github/workflows').glob('*.yml')) + sorted((repo/'.github/workflows').glob('*.yaml'))
    workflow_notes = []
    if not workflows:
        warnings.append('no GitHub workflows found')
    for wf in workflows:
        text = read(wf)
        uses_spec = 'Deimos.spec' in text
        workflow_notes.append({'path': str(wf.relative_to(repo)), 'uses_deimos_spec': uses_spec})
        if ('pyinstaller' in text.lower()) and not uses_spec:
            blockers.append(f'workflow runs pyinstaller without Deimos.spec: {wf.relative_to(repo)}')
    is_windows = platform.system().lower() == 'windows'
    if not is_windows:
        warnings.append('not running on Windows; pywin32/PyInstaller executable validation is preflight-only')
    uv_path = shutil.which('uv')
    if not uv_path:
        warnings.append('uv command not found on PATH; expected build setup uses uv')
    report = {
        'phase': 33,
        'repo': str(repo),
        'platform': platform.platform(),
        'is_windows': is_windows,
        'uv_on_path': bool(uv_path),
        'uv_path': uv_path,
        'expected_commands': [
            'uv python install',
            'uv sync --group dev',
            'uv run --group dev pyinstaller --noconfirm --clean Deimos.spec'
        ],
        'workflow_notes': workflow_notes,
        'blockers': blockers,
        'warnings': warnings,
        'windows_build_preflight_ready': not blockers,
    }
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding='utf-8')
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if blockers else 0

if __name__ == '__main__':
    raise SystemExit(main())
