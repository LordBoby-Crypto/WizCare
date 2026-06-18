#!/usr/bin/env python3
"""Validate Deimos traversal zone/entity references against local traversalData and Wizard101 seed data."""
from __future__ import annotations
import json, re, sys
from pathlib import Path
from typing import Any


def norm(s: str) -> str:
    return re.sub(r'[^a-z0-9]+',' ',s.lower()).strip()


def load_json_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists(): return []
    data=json.loads(path.read_text(encoding='utf-8'))
    return data if isinstance(data,list) else []


def load_traversal(repo: Path) -> dict[str, Any]:
    td=repo/'libs'/'wizsprinter'/'wizwalker'/'extensions'/'wizsprinter'/'traversalData'
    result={'display_zones':[], 'zone_map_entries':[], 'object_locations':[], 'unique_object_locations':[], 'gates':[]}
    for key,file in [('display_zones','displayZones.txt'),('zone_map_entries','zoneMap.txt'),('object_locations','objectLocations.txt'),('unique_object_locations','uniqueObjectLocations.txt'),('gates','gates_list.txt')]:
        p=td/file
        if p.exists():
            result[key]=[line.strip() for line in p.read_text(encoding='utf-8',errors='ignore').splitlines() if line.strip()]
    return result


def main() -> int:
    if len(sys.argv) < 3:
        print('usage: deimos_zone_entity_link_validator.py <repo> <wizard101-data-dir> [out.json]', file=sys.stderr); return 2
    repo=Path(sys.argv[1]).resolve(); data_dir=Path(sys.argv[2]).resolve(); out=Path(sys.argv[3]) if len(sys.argv)>3 else None
    trav=load_traversal(repo)
    seed=data_dir/'seed'
    zones=load_json_list(seed/'zones.json')
    worlds=load_json_list(seed/'worlds.json')
    enemies=load_json_list(seed/'enemies.json')
    npcs=load_json_list(seed/'npcs.json')
    zone_names={norm(z.get('name','')) for z in zones if z.get('name')}
    world_names={norm(w.get('name','')) for w in worlds if w.get('name')}
    entity_names={norm(e.get('name','')) for e in enemies+npcs if e.get('name')}
    display_norm={norm(x) for x in trav['display_zones']}
    zone_hits=sorted([x for x in display_norm if x in zone_names or x in world_names])
    zone_missing=sorted([x for x in display_norm if x and x not in zone_names and x not in world_names])[:300]
    object_lines=trav['object_locations'] + trav['unique_object_locations']
    object_tokens=[]
    for line in object_lines:
        # best-effort extraction: first pipe/comma/tab-delimited name-ish token
        token=re.split(r'[|,\t]', line)[0].strip().strip('"\'')
        if token and re.search(r'[A-Za-z]', token): object_tokens.append(token)
    object_norm={norm(x) for x in object_tokens}
    entity_hits=sorted([x for x in object_norm if x in entity_names])
    report={
        'repo': str(repo),
        'data_dir': str(data_dir),
        'traversal_counts': {k:len(v) for k,v in trav.items()},
        'wizard101_seed_counts': {'worlds':len(worlds),'zones':len(zones),'enemies':len(enemies),'npcs':len(npcs)},
        'display_zone_links': {'matched_count':len(zone_hits),'unmatched_count':max(0,len(display_norm)-len(zone_hits)),'matched_sample':zone_hits[:80],'unmatched_sample':zone_missing},
        'object_entity_links': {'object_name_candidates':len(object_norm),'matched_entities':len(entity_hits),'matched_sample':entity_hits[:80]},
        'policy': 'Unmatched traversal zones are not necessarily bugs; they usually mean the Wizard101 knowledge base needs more zone/location imports before route validation can be strict.'
    }
    text=json.dumps(report,indent=2,ensure_ascii=False)
    if out: out.parent.mkdir(parents=True,exist_ok=True); out.write_text(text+'\n',encoding='utf-8')
    else: print(text)
    return 0
if __name__=='__main__': raise SystemExit(main())
