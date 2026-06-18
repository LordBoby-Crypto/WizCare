#!/usr/bin/env python3
from __future__ import annotations
import json, re, sys
from pathlib import Path
from datetime import datetime, timezone

def read(p): return p.read_text(encoding='utf-8', errors='replace')
def parse_spec(repo: Path):
    spec = read(repo/'Deimos.spec')
    datas = re.findall(r"\(['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\)", spec)
    hidden = [m.group(1) for m in re.finditer(r"collect_submodules\(['\"]([^'\"]+)['\"]\)", spec)]
    explicit = re.findall(r"['\"]([^'\"]+)['\"]", re.search(r"\+ \[([^\]]*)\]", spec, re.S).group(1) if re.search(r"\+ \[([^\]]*)\]", spec, re.S) else '')
    return {'datas':datas,'collect_submodules':hidden,'explicit_hiddenimports':explicit,'has_manifest':"manifest='app.manifest'" in spec or 'manifest="app.manifest"' in spec,'has_version_file':"version='version_info.txt'" in spec or 'version="version_info.txt"' in spec,'has_icon':"icon='Deimos-logo.ico'" in spec or 'icon="Deimos-logo.ico"' in spec}
def workflow_info(repo: Path):
    out=[]
    for p in sorted((repo/'.github'/'workflows').glob('*.yml')):
        txt=read(p)
        out.append({'file':str(p.relative_to(repo)),'uses_deimos_spec':'Deimos.spec' in txt,'uses_raw_pyinstaller_deimos_py':bool(re.search(r'pyinstaller[^\n]*Deimos\.py',txt)),'checks_dist_exe':'dist/Deimos.exe' in txt,'mentions_locale':'locale' in txt,'mentions_sha256':'sha256' in txt.lower()})
    return out
def version_info(repo: Path):
    d=read(repo/'Deimos.py'); py=read(repo/'pyproject.toml')
    dv=re.search(r"tool_version:\s*str\s*=\s*['\"]([^'\"]+)", d); pv=re.search(r"^version\s*=\s*['\"]([^'\"]+)", py, re.M)
    return {'Deimos.py':dv.group(1) if dv else None,'pyproject.toml':pv.group(1) if pv else None,'consistent':bool(dv and pv and dv.group(1)==pv.group(1))}
def main():
    repo=Path(sys.argv[1]) if len(sys.argv)>1 else Path.cwd()
    spec=parse_spec(repo); ver=version_info(repo); workflows=workflow_info(repo)
    required=['Deimos.py','Deimos.spec','locale/en.lang','locale/zh.lang','version_info.txt','app.manifest','LICENSE','pyproject.toml','src/gui/bot_validation.py','src/gui/tab_actions.py']
    optional_binary_assets=['Deimos-logo.ico','Deimos-logo.png']
    presence={f:(repo/f).exists() for f in required}
    blockers=[]; warnings=[]
    if not all(presence.values()): blockers += [f'missing required file: {k}' for k,v in presence.items() if not v]
    datas=dict(spec['datas'])
    if 'locale' not in datas:
        blockers.append('Deimos.spec datas does not include locale')
    for item in optional_binary_assets:
        if not (repo/item).exists():
            warnings.append(f'optional binary asset not source-tracked: {item}')
        if item in datas:
            warnings.append(f'Deimos.spec still bundles optional binary asset: {item}')
    for mod in ['wizwalker','wizwalker.extensions.wizsprinter','wizsprinter','lark']:
        if mod not in spec['collect_submodules']: warnings.append(f'Deimos.spec does not collect_submodules({mod})')
    if not spec['has_manifest']: blockers.append('Deimos.spec missing app.manifest')
    if not spec['has_version_file']: blockers.append('Deimos.spec missing version_info.txt')
    if spec['has_icon']:
        warnings.append('Deimos.spec uses optional Deimos-logo.ico icon')
    raw=[w for w in workflows if w['uses_raw_pyinstaller_deimos_py']]
    if raw: warnings.append('workflows still using raw PyInstaller Deimos.py: '+', '.join(w['file'] for w in raw))
    if not ver['consistent']: blockers.append(f"version mismatch: Deimos.py={ver['Deimos.py']} pyproject.toml={ver['pyproject.toml']}")
    out={'generated_at':datetime.now(timezone.utc).isoformat(),'version':ver,'required_files':presence,'pyinstaller_spec':spec,'workflows':workflows,'blockers':blockers,'warnings':warnings,'build_artifact_ready_basic':not blockers}
    print(json.dumps(out,indent=2))
    return 1 if blockers else 0
if __name__=='__main__': raise SystemExit(main())
