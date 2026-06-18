#!/usr/bin/env python3
"""Run no-side-effect import/build smoke checks for patched Deimos modules.

This intentionally favors AST parsing and bytecode compilation over importing GUI
modules that may require PyQt6, Windows APIs, or game clients. It may import
src.gui.bot_validation because that module is dependency-light by design.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import py_compile
import sys
import tempfile
from pathlib import Path


def compile_file(path: Path) -> dict:
    item = {"path": str(path), "exists": path.exists(), "compile_ok": False, "syntax_ok": False, "error": None}
    if not path.exists():
        item["error"] = "missing"
        return item
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        item["syntax_ok"] = True
        with tempfile.TemporaryDirectory() as tmp:
            py_compile.compile(str(path), cfile=str(Path(tmp) / (path.name + ".pyc")), doraise=True)
        item["compile_ok"] = True
    except Exception as exc:  # noqa: BLE001 - report only
        item["error"] = f"{type(exc).__name__}: {exc}"
    return item


def import_bot_validation(repo: Path) -> dict:
    path = repo / "src" / "gui" / "bot_validation.py"
    result = {"path": str(path), "attempted": path.exists(), "import_ok": False, "smoke_tests": [], "error": None}
    if not path.exists():
        result["error"] = "missing"
        return result
    try:
        spec = importlib.util.spec_from_file_location("phase32_bot_validation", path)
        if spec is None or spec.loader is None:
            raise RuntimeError("could not create module spec")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        validate = module.validate_bot_script
        cases = {
            "empty": "",
            "metadata_only": "@clients: p1\n# comment",
            "basic": "@clients: p1\nwait 1\ntozone Wizard City",
            "bad_wait": "wait -5",
        }
        for name, script in cases.items():
            r = validate(script)
            result["smoke_tests"].append({"name": name, "ok": bool(r.ok), "errors": len(r.errors), "warnings": len(r.warnings)})
        result["import_ok"] = True
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def check(repo: Path) -> dict:
    files = [
        repo / "Deimos.py",
        repo / "src" / "gui" / "bot_validation.py",
        repo / "src" / "gui" / "tab_actions.py",
        repo / "src" / "gui" / "commands.py",
        repo / "src" / "command_parser.py",
    ]
    compile_results = [compile_file(path) for path in files]
    import_result = import_bot_validation(repo)
    blockers = []
    for item in compile_results:
        if not item["compile_ok"]:
            blockers.append(f"compile failed: {item['path']} ({item['error']})")
    if not import_result["import_ok"]:
        blockers.append(f"bot_validation import smoke failed: {import_result['error']}")
    return {"ok": not blockers, "blockers": blockers, "compiled_files": compile_results, "bot_validation_import": import_result}


def main() -> int:
    repo = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    out = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else None
    result = check(repo)
    text = json.dumps(result, indent=2, sort_keys=True)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0 if result["ok"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
