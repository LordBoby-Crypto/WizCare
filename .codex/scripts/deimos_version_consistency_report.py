#!/usr/bin/env python3
"""Report and optionally fix Deimos version consistency across Deimos.py and pyproject.toml."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

TOOL_RE = re.compile(r"tool_version:\s*str\s*=\s*['\"]([^'\"]+)['\"]")
PYPROJECT_RE = re.compile(r"^version\s*=\s*['\"]([^'\"]+)['\"]", re.M)

def read(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace')

def find_versions(repo: Path) -> dict:
    deimos_py = repo / 'Deimos.py'
    pyproject = repo / 'pyproject.toml'
    deimos_text = read(deimos_py) if deimos_py.exists() else ''
    pyproject_text = read(pyproject) if pyproject.exists() else ''
    tool = (TOOL_RE.search(deimos_text) or [None, None])[1] if TOOL_RE.search(deimos_text) else None
    project = (PYPROJECT_RE.search(pyproject_text) or [None, None])[1] if PYPROJECT_RE.search(pyproject_text) else None
    return {
        'repo': str(repo),
        'deimos_py_exists': deimos_py.exists(),
        'pyproject_exists': pyproject.exists(),
        'tool_version': tool,
        'pyproject_version': project,
        'consistent': bool(tool and project and tool == project),
        'recommended_action': 'none' if tool and project and tool == project else 'set pyproject.toml version to Deimos.py tool_version unless release owner chooses a new release version and updates both files together',
    }

def fix(repo: Path) -> dict:
    report = find_versions(repo)
    if report['tool_version'] and report['pyproject_version'] and report['tool_version'] != report['pyproject_version']:
        pyproject = repo / 'pyproject.toml'
        text = read(pyproject)
        text = re.sub(r"(^version\s*=\s*)['\"][^'\"]+['\"]", rf"\g<1>\"{report['tool_version']}\"", text, count=1, flags=re.M)
        pyproject.write_text(text, encoding='utf-8')
        report = find_versions(repo)
        report['fixed'] = True
    else:
        report['fixed'] = False
    return report

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('repo', type=Path)
    ap.add_argument('--fix', action='store_true')
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    result = fix(args.repo) if args.fix else find_versions(args.repo)
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + '\n', encoding='utf-8')
    print(text)
    raise SystemExit(0 if result.get('consistent') else 1)
