#!/usr/bin/env python3
"""Static parser-aware validator for Deimos raw bot and DeimosLang-like files.

It deliberately avoids importing or executing project code. It validates common command shapes,
client selectors, xyz/orient tuples, zone strings, wait conditions, and combat markers.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
from typing import Any

RAW_ALIASES = {
    'kill','killbot','stop','stopbot','end','exit','sleep','wait','delay','log','debug','print',
    'teleport','tp','setpos','walkto','goto','sendkey','press','presskey','waitfordialog','waitfordialogue',
    'waitforbattle','waitforcombat','waitforzonechange','wait_for_zone_change','waitforfree','usepotion',
    'buypotions','refillpotions','buypots','refillpots','logoutandin','relog','click','clickwindow',
    'waitforwindow','waitforpath','friendtp','friendteleport','entitytp','entityteleport','tozone','to_zone',
    'glideto','rotatingglideto','orbit','lookat','setorient'
}
DEIMOSLANG_ALIASES = RAW_ALIASES | {
    'loadplaystyle','turncam','setcamyaw','nav','navtp','getdeck','setdeck','selectfriend','choosefriend',
    'plustp','plusteleport','minustp','minusteleport','autopet','toggleautopet','loggoal','logquest','logzone',
    'togglecombat','togglecombatmode','cursor','movecursor','mousexy','movemouse','cursorwindow','mousewindow',
    'block','call','loop','while','until','if','elif','else','mixin','return','break','con','set','setvar','var'
}
GLOBAL_COMMANDS = {'kill','killbot','stop','stopbot','end','exit','sleep','wait','delay','log','debug','print','glideto','rotatingglideto','orbit','lookat','setpos','setorient'}
CLIENT_SELECTOR_RE = re.compile(r'^(except\s+)?(mass|p\d+(?::p\d+)*|p\d+|any|anyplayer|anyclient|sameany|sameanyplayer|sameanyclient)$', re.I)
XYZ_RE = re.compile(r'\bxyz\s*\(([^)]*)\)', re.I)
ORIENT_RE = re.compile(r'\borient\s*\(([^)]*)\)', re.I)
MARKER_RE = re.compile(r'^\s*###\s*p\s*(\d+)\b', re.I)


def load_zones(repo: Path) -> set[str]:
    zones: set[str] = set()
    td = repo / 'libs' / 'wizsprinter' / 'wizwalker' / 'extensions' / 'wizsprinter' / 'traversalData'
    for name in ['displayZones.txt','zoneMap.txt']:
        path = td / name
        if not path.exists():
            continue
        for line in path.read_text(encoding='utf-8', errors='ignore').splitlines():
            line=line.strip()
            if not line or line.startswith('#'):
                continue
            for part in re.split(r'[|,\t]', line):
                part=part.strip().strip('"\'')
                if len(part) >= 2 and re.search(r'[A-Za-z]', part):
                    zones.add(part.lower())
    return zones


def candidate_files(repo: Path) -> list[Path]:
    exts = {'.txt','.bot','.dl','.dms','.script','.cfg','.conf'}
    ignore_parts = {'.git','__pycache__','.venv','venv','node_modules','traversalData'}
    files=[]
    for p in repo.rglob('*'):
        if not p.is_file() or any(part in ignore_parts for part in p.parts):
            continue
        if p.suffix.lower() in exts:
            rel = str(p.relative_to(repo)).replace('\\','/')
            if '/traversalData/' in '/' + rel or rel.startswith('libs/wizsprinter/wizwalker/extensions/wizsprinter/traversalData/'):
                continue
            try:
                txt = p.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            low = txt.lower()
            if any(cmd in low for cmd in ['###p','tozone','xyz(','waitfor','teleport','setdeck','loadplaystyle','goto','walkto','entitytp']):
                files.append(p)
    return files


def split_tokens(line: str) -> list[str]:
    # lightweight token splitter preserving quoted strings and bracket/path chunks enough for static checks
    return re.findall(r'"[^"]*"|\'[^\']*\'|\[[^\]]*\]|\S+', line)


def check_triplets(line: str, regex: re.Pattern[str], kind: str, warnings: list[str]) -> None:
    for m in regex.finditer(line):
        parts = [x.strip() for x in m.group(1).split(',')]
        if len(parts) != 3:
            warnings.append(f'{kind} tuple should contain exactly 3 comma-separated values: {m.group(0)}')
        for part in parts:
            if not part:
                warnings.append(f'{kind} tuple contains an empty value: {m.group(0)}')


def validate_line(line: str, zones: set[str]) -> dict[str, Any] | None:
    raw = line.strip()
    if not raw or raw.startswith('#') or raw.startswith('//'):
        return None
    warnings: list[str] = []
    errors: list[str] = []
    marker = MARKER_RE.match(raw)
    if marker:
        n = int(marker.group(1))
        if n < 1:
            errors.append('combat marker must be ###p1 or higher')
        return {'kind':'combat-marker','command':'###p','errors':errors,'warnings':warnings}
    toks = split_tokens(raw)
    if not toks:
        return None
    first = toks[0].lower().strip('"\'')
    command = first
    selector = None
    if CLIENT_SELECTOR_RE.match(first) and len(toks) > 1:
        selector = first
        command = toks[1].lower().strip('"\'')
    elif first == 'except' and len(toks) > 2:
        selector = ' '.join(toks[:2]).lower()
        command = toks[2].lower().strip('"\'')
    if command not in DEIMOSLANG_ALIASES:
        # Avoid noise for plain data files; only warn if line looks command-like.
        if '(' in raw or raw.lower().startswith(('p1','p2','p3','p4','mass','except')):
            warnings.append(f'unknown or unsupported command token: {command}')
    check_triplets(raw, XYZ_RE, 'xyz', warnings)
    check_triplets(raw, ORIENT_RE, 'orient', warnings)
    lower = raw.lower()
    if command in {'sleep','wait','delay'}:
        nums = re.findall(r'-?\d+(?:\.\d+)?', raw)
        if not nums:
            errors.append('sleep/wait/delay requires a numeric seconds argument')
        elif float(nums[-1]) < 0:
            errors.append('sleep/wait/delay seconds must be non-negative')
    if command in {'goto','walkto','glideto','rotatingglideto','lookat'} and 'xyz' not in lower:
        warnings.append(f'{command} usually requires xyz(x,y,z)')
    if command in {'setorient'} and 'orient' not in lower:
        warnings.append('setorient usually requires orient(pitch,roll,yaw)')
    if command in {'sendkey','press','presskey'} and len(toks) < (3 if selector else 2):
        errors.append('sendkey/press requires a key argument')
    if command in {'waitforzonechange','wait_for_zone_change'}:
        if ' from ' in f' {lower} ' or ' to ' in f' {lower} ':
            z = toks[-1].strip('"\'').lower()
            if zones and z not in zones:
                warnings.append(f'zone string not found in traversalData aliases: {toks[-1]}')
    if command in {'tozone','to_zone'}:
        arg = toks[-1].strip('"\'').lower() if len(toks) >= 2 else ''
        if not arg:
            errors.append('tozone requires a zone/path argument')
        elif zones and arg not in zones and '/' not in arg:
            warnings.append(f'tozone target not found as display zone alias: {toks[-1]}')
    if selector and not CLIENT_SELECTOR_RE.match(selector):
        warnings.append(f'non-standard client selector: {selector}')
    return {'kind':'command-line','selector':selector,'command':command,'errors':errors,'warnings':warnings}


def validate_file(path: Path, repo: Path, zones: set[str]) -> dict[str, Any]:
    rel = str(path.relative_to(repo))
    txt = path.read_text(encoding='utf-8', errors='ignore')
    line_results=[]; errors=[]; warnings=[]; markers=[]
    for idx,line in enumerate(txt.splitlines(),1):
        res=validate_line(line,zones)
        if not res:
            continue
        res['line']=idx
        line_results.append(res)
        if res['kind']=='combat-marker':
            markers.append((idx,line.strip()))
        for e in res['errors']:
            errors.append({'line':idx,'message':e})
        for w in res['warnings']:
            warnings.append({'line':idx,'message':w})
    marker_nums=[]
    for idx,text in markers:
        m=MARKER_RE.match(text)
        if m:
            marker_nums.append(int(m.group(1)))
    duplicate_markers=sorted({n for n in marker_nums if marker_nums.count(n)>1})
    for n in duplicate_markers:
        warnings.append({'line':None,'message':f'duplicate combat marker ###p{n}'})
    return {
        'file': rel,
        'commands_detected': len([r for r in line_results if r['kind']=='command-line']),
        'combat_markers_detected': len(markers),
        'duplicate_markers': duplicate_markers,
        'errors': errors,
        'warnings': warnings,
        'sample': line_results[:25],
    }


def main() -> int:
    if len(sys.argv) < 2:
        print('usage: deimos_parser_aware_bot_validator.py <repo> [out.json]', file=sys.stderr)
        return 2
    repo=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]) if len(sys.argv)>2 else None
    zones=load_zones(repo)
    files=candidate_files(repo)
    reports=[validate_file(p,repo,zones) for p in files]
    report={
        'repo': str(repo),
        'zone_aliases_loaded': len(zones),
        'candidate_files': len(files),
        'files': reports,
        'totals': {
            'commands_detected': sum(r['commands_detected'] for r in reports),
            'combat_markers_detected': sum(r['combat_markers_detected'] for r in reports),
            'errors': sum(len(r['errors']) for r in reports),
            'warnings': sum(len(r['warnings']) for r in reports),
        },
        'policy': 'Static validation only. Warnings are review prompts; errors block parser-aware automation edits until resolved or explained.',
    }
    text=json.dumps(report,indent=2,ensure_ascii=False)
    if out:
        out.parent.mkdir(parents=True,exist_ok=True); out.write_text(text+'\n',encoding='utf-8')
    else: print(text)
    return 0
if __name__=='__main__': raise SystemExit(main())
