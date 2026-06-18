#!/usr/bin/env python3
"""Conservative release-readiness report for Deimos repos."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

def read(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace') if path.exists() else ''

def version_report(repo: Path) -> dict:
    d = read(repo/'Deimos.py')
    p = read(repo/'pyproject.toml')
    tm = re.search(r"tool_version:\s*str\s*=\s*['\"]([^'\"]+)['\"]", d)
    pm = re.search(r"^version\s*=\s*['\"]([^'\"]+)['\"]", p, re.M)
    return {'tool_version': tm.group(1) if tm else None, 'pyproject_version': pm.group(1) if pm else None, 'consistent': bool(tm and pm and tm.group(1)==pm.group(1))}

def locale_report(repo: Path) -> dict:
    def keys(path: Path):
        out=[]
        for line in read(path).splitlines():
            s=line.strip()
            if not s or s.startswith('#') or '=' not in s: continue
            out.append(s.split('=',1)[0].strip())
        return out
    en=keys(repo/'locale/en.lang'); zh=keys(repo/'locale/zh.lang')
    return {'en_keys': len(en), 'zh_keys': len(zh), 'missing_in_zh': sorted(set(en)-set(zh)), 'missing_in_en': sorted(set(zh)-set(en)), 'consistent': set(en)==set(zh)}

def files_report(repo: Path) -> dict:
    required=['Deimos.py','pyproject.toml','Deimos.spec','src/gui/tab_actions.py','src/gui/bot_validation.py','locale/en.lang','locale/zh.lang']
    return {'required_files': {x:(repo/x).exists() for x in required}}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('repo', type=Path); ap.add_argument('--out', type=Path); args=ap.parse_args()
    report={'repo': str(args.repo), 'version': version_report(args.repo), 'locale': locale_report(args.repo), 'files': files_report(args.repo)}
    blockers=[]
    if not report['version']['consistent']: blockers.append('version_mismatch')
    if not report['locale']['consistent']: blockers.append('locale_key_mismatch')
    for k,v in report['files']['required_files'].items():
        if not v: blockers.append('missing_'+k)
    report['release_ready_basic']=not blockers
    report['blockers']=blockers
    text=json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True); args.out.write_text(text+'\n', encoding='utf-8')
    print(text)
    raise SystemExit(0 if not blockers else 1)
if __name__=='__main__': main()
