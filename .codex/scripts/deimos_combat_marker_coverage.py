#!/usr/bin/env python3
"""Analyze Deimos/Sprinty combat config marker coverage in repository text config files."""
from __future__ import annotations
import json, re, sys
from pathlib import Path
MARKER=re.compile(r'^\s*###\s*p\s*(\d+)\b', re.I)

def candidate_files(repo: Path):
    for p in repo.rglob('*'):
        if p.is_file() and p.suffix.lower() in {'.txt','.cfg','.conf','.bot'}:
            txt=p.read_text(encoding='utf-8',errors='ignore')
            if '###' in txt or 'spell(' in txt or '@ enemy' in txt or '@ boss' in txt:
                yield p, txt

def analyze(path: Path, repo: Path, txt: str):
    markers=[]; sections={}; cur=None; buf=[]
    for i,line in enumerate(txt.splitlines(),1):
        m=MARKER.match(line)
        if m:
            if cur is not None: sections[cur]='\n'.join(buf).strip(); buf=[]
            cur=int(m.group(1)); markers.append({'line':i,'client_index':cur,'raw':line.strip()}); continue
        if cur is not None: buf.append(line)
    if cur is not None: sections[cur]='\n'.join(buf).strip()
    duplicates=sorted({m['client_index'] for m in markers if [x['client_index'] for x in markers].count(m['client_index'])>1})
    empty=[k for k,v in sections.items() if not v]
    return {'file':str(path.relative_to(repo)), 'markers':markers, 'marker_count':len(markers), 'duplicates':duplicates, 'empty_sections':empty, 'has_default_config_without_markers': bool(not markers and txt.strip())}

def main():
    if len(sys.argv)<2:
        print('usage: deimos_combat_marker_coverage.py <repo> [out.json]',file=sys.stderr); return 2
    repo=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]) if len(sys.argv)>2 else None
    files=[analyze(p,repo,t) for p,t in candidate_files(repo)]
    report={'repo':str(repo),'files':files,'totals':{'files':len(files),'marker_files':sum(1 for f in files if f['marker_count']),'markers':sum(f['marker_count'] for f in files),'duplicate_marker_files':sum(1 for f in files if f['duplicates']),'empty_section_files':sum(1 for f in files if f['empty_sections'])},'policy':'Files without ###p markers may be valid fallback configs. Duplicate or empty marked sections require review before Codex edits combat configs.'}
    text=json.dumps(report,indent=2,ensure_ascii=False)
    if out: out.parent.mkdir(parents=True,exist_ok=True); out.write_text(text+'\n',encoding='utf-8')
    else: print(text)
    return 0
if __name__=='__main__': raise SystemExit(main())
