#!/usr/bin/env python3
"""Aggregate Phase 32 local build smoke and dependency readiness reports."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def run(script: Path, repo: Path, out: Path) -> tuple[int, dict]:
    proc = subprocess.run([sys.executable, str(script), str(repo), str(out)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        data = json.loads(out.read_text(encoding="utf-8"))
    except Exception:
        data = {"ok": False, "error": "could not read child report", "stdout": proc.stdout, "stderr": proc.stderr}
    return proc.returncode, data


def main() -> int:
    repo = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    out = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else repo / ".codex" / "reports" / "phase32-local-prebuild-report.json"
    scripts = Path(__file__).resolve().parent
    tmp_dir = out.parent
    tmp_dir.mkdir(parents=True, exist_ok=True)
    dep_code, dep = run(scripts / "deimos_local_dependency_readiness.py", repo, tmp_dir / "phase32-local-dependency-readiness.json")
    smoke_code, smoke = run(scripts / "deimos_import_smoke_report.py", repo, tmp_dir / "phase32-import-smoke-report.json")
    blockers = []
    warnings = []
    if not dep.get("ok"):
        blockers.extend(dep.get("blockers", []))
    warnings.extend(dep.get("warnings", []))
    if not smoke.get("ok"):
        blockers.extend(smoke.get("blockers", []))
    result = {
        "ok": not blockers,
        "local_machine_build_ready": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "dependency_report": dep,
        "import_smoke_report": smoke,
        "next_safe_commands": [
            "uv python install",
            "uv sync --group dev",
            "uv run python .codex/scripts/deimos_import_smoke_report.py . .codex/reports/phase32-import-smoke-report.json",
            "uv run --group dev pyinstaller --noconfirm --clean Deimos.spec",
        ],
    }
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
