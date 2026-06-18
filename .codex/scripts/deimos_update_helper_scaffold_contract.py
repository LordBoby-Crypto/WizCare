#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED = [
    Path('libs/updater_helper/deimos_updater_helper.py'),
    Path('libs/updater_helper/README.md'),
]
FORBIDDEN_SNIPPETS = ['os.replace(', 'shutil.move(', 'subprocess.Popen(', 'CreateProcess', '--install-now']

def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    blockers=[]; warnings=[]
    for rel in REQUIRED:
        if not (root/rel).exists(): blockers.append(f'missing {rel}')
    helper = root/'libs/updater_helper/deimos_updater_helper.py'
    if helper.exists():
        text=helper.read_text(encoding='utf-8')
        for snippet in FORBIDDEN_SNIPPETS:
            if snippet in text: blockers.append(f'forbidden install/launch snippet present: {snippet}')
        for required in ['--manifest','--wait-pid','--log','--dry-run','EXIT_UNSAFE_OPERATION_BLOCKED']:
            if required not in text: blockers.append(f'helper missing contract token: {required}')
        if 'Phase 42 helper scaffold only allows --dry-run' not in text:
            blockers.append('helper does not explicitly require dry-run')
    result={'phase':42,'check':'update_helper_scaffold_contract','passed':not blockers,'blockers':blockers,'warnings':warnings}
    out = root/'.codex/reports/phase42-update-helper-scaffold-contract.json'
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 0 if not blockers else 1
if __name__ == '__main__': raise SystemExit(main())
