#!/usr/bin/env python3
from __future__ import annotations
import json, re, sys
from pathlib import Path

def main():
    repo=Path(sys.argv[1]) if len(sys.argv)>1 else Path.cwd()
    rows=[]
    for p in sorted((repo/'.github'/'workflows').glob('*.yml')):
        txt=p.read_text(encoding='utf-8',errors='replace')
        rows.append({
          'file':str(p.relative_to(repo)),
          'triggers': [line.strip() for line in txt.splitlines() if line.strip().startswith(('push:','pull_request:','workflow_dispatch:'))],
          'uses_uv': 'uv sync' in txt,
          'uses_deimos_spec': 'Deimos.spec' in txt,
          'uses_raw_pyinstaller': bool(re.search(r'pyinstaller[^\n]*Deimos\.py', txt)),
          'verifies_dist_exe': 'dist/Deimos.exe' in txt,
          'packages_release_zip': 'Compress-Archive' in txt,
          'uploads_artifact_or_release': 'upload-artifact' in txt or 'action-gh-release' in txt,
        })
    print(json.dumps({'workflow_count':len(rows),'workflows':rows}, indent=2))
if __name__=='__main__': main()
