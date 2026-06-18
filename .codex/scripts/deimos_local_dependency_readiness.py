#!/usr/bin/env python3
"""Check local build/dependency readiness for Deimos without performing a build.

This checker is intentionally conservative. It does not install packages and it
must not mutate the repo. It reports whether the current machine looks capable
of running the repo's normal uv/PyInstaller build flow.
"""
from __future__ import annotations

import importlib.util
import json
import platform
import re
import shutil
import sys
import tomllib
from pathlib import Path


def _version_tuple(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", text)[:3])


def check(repo: Path) -> dict:
    pyproject = repo / "pyproject.toml"
    blockers: list[str] = []
    warnings: list[str] = []
    info: dict = {
        "repo": str(repo),
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "is_windows": platform.system().lower() == "windows",
        "uv_path": shutil.which("uv"),
        "pyinstaller_importable": importlib.util.find_spec("PyInstaller") is not None,
        "pyqt6_importable": importlib.util.find_spec("PyQt6") is not None,
        "pywin32_importable": importlib.util.find_spec("win32gui") is not None,
    }
    if not pyproject.exists():
        blockers.append("missing pyproject.toml")
        return {"ok": False, "blockers": blockers, "warnings": warnings, **info}

    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    project = data.get("project", {})
    requires_python = project.get("requires-python", "")
    dependencies = project.get("dependencies", [])
    dev = data.get("dependency-groups", {}).get("dev", [])
    info.update({
        "requires_python": requires_python,
        "dependency_count": len(dependencies),
        "dev_dependencies": dev,
        "has_pyinstaller_dev_dependency": any("pyinstaller" in str(item).lower() for item in dev),
        "has_pyqt6_dependency": any(str(item).lower().startswith("pyqt6") for item in dependencies),
        "has_pywin32_dependency": any("pywin32" in str(item).lower() for item in dependencies),
        "workspace_members": data.get("tool", {}).get("uv", {}).get("workspace", {}).get("members", []),
    })

    m = re.search(r">=\s*([0-9]+(?:\.[0-9]+){0,2})", requires_python)
    if m and sys.version_info < _version_tuple(m.group(1)):
        blockers.append(f"current Python {platform.python_version()} does not satisfy {requires_python}")

    if not info["uv_path"]:
        blockers.append("uv is not installed or not on PATH")
    if not info["has_pyinstaller_dev_dependency"]:
        blockers.append("pyinstaller is not listed in dependency-groups.dev")
    if not info["has_pyqt6_dependency"]:
        warnings.append("PyQt6 dependency was not found in project dependencies")
    if info["has_pywin32_dependency"] and not info["is_windows"]:
        warnings.append("Windows-only pywin32 modules are expected to be unavailable on this platform")
    if not info["pyinstaller_importable"]:
        warnings.append("PyInstaller is not importable in this environment; uv sync --group dev should install it")
    if not info["pyqt6_importable"]:
        warnings.append("PyQt6 is not importable in this environment; GUI import smoke should be run after uv sync")

    missing_workspace = [m for m in info["workspace_members"] if not (repo / m).exists()]
    info["missing_workspace_members"] = missing_workspace
    if missing_workspace:
        blockers.append("missing uv workspace members: " + ", ".join(missing_workspace))

    expected = ["Deimos.py", "Deimos.spec", "Deimos-logo.ico", "Deimos-logo.png", "locale", "app.manifest", "version_info.txt"]
    missing = [name for name in expected if not (repo / name).exists()]
    info["missing_build_inputs"] = missing
    if missing:
        blockers.append("missing build inputs: " + ", ".join(missing))

    return {"ok": not blockers, "blockers": blockers, "warnings": warnings, **info}


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
