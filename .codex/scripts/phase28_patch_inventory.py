#!/usr/bin/env python3
"""Report what Phase 28 patch files are present and what they touch."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("patch_dir", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    patch = args.patch_dir
    files = sorted([p for p in patch.rglob("*") if p.is_file()])
    report = {
        "patch_dir": str(patch),
        "file_count": len(files),
        "files": [str(p.relative_to(patch)) for p in files],
        "touches_runtime_source": any(str(p.relative_to(patch)).startswith("src/") for p in files),
        "touches_locale": any(str(p.relative_to(patch)).startswith("locale/") for p in files),
    }
    output = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
