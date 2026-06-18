#!/usr/bin/env python3
from __future__ import annotations
import ast, json, sys
from pathlib import Path

def main() -> int:
    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else repo/'.codex/reports/phase41-update-helper-contract.json'
    src = repo/'src/update_system.py'
    text = src.read_text(encoding='utf-8')
    blockers=[]; warnings=[]
    required = [
        'PHASE41_UPDATER_HELPER_SPECIFICATION',
        'build_update_helper_contract',
        'build_update_helper_manifest',
        'validate_update_helper_manifest',
        'HELPER_ALLOWED_EXIT_CODES',
        'HELPER_SPEC_VERSION',
        'HELPER_MANIFEST_NAME',
    ]
    for token in required:
        if token not in text:
            blockers.append(f'missing {token}')
    tree = ast.parse(text)
    forbidden_calls=[]
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f=node.func
            name=''
            if isinstance(f, ast.Attribute):
                name=f.attr
                if isinstance(f.value, ast.Name):
                    name=f.value.id+'.'+name
            elif isinstance(f, ast.Name):
                name=f.id
            if name in {'os.replace','os.remove','subprocess.Popen','subprocess.run','subprocess.call'}:
                forbidden_calls.append(name)
    if forbidden_calls:
        blockers.append('update_system.py contains forbidden install/launch calls: '+', '.join(sorted(set(forbidden_calls))))
    if 'HELPER_SPEC_REVIEW_ONLY = True' not in text:
        blockers.append('helper spec must remain review-only')
    report={'phase':41,'script':'deimos_update_helper_contract','passed':not blockers,'blockers':blockers,'warnings':warnings,'source':str(src)}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if not blockers else 1
if __name__=='__main__': raise SystemExit(main())
