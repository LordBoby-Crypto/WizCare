from __future__ import annotations
import importlib.util, json, sys, tempfile
from pathlib import Path


def load_module(root: Path):
    spec = importlib.util.spec_from_file_location("deimos_update_system_smoke_target", root / "src" / "update_system.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load src/update_system.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main(repo_root: str, out_path: str) -> int:
    root = Path(repo_root)
    report = {"blockers": [], "checks": {}}
    try:
        mod = load_module(root)
        report["checks"]["normalize_version"] = mod.normalize_version("v3.13.1") == (3, 13, 1)
        report["checks"]["is_newer"] = mod.is_newer_version("3.14.0", "3.13.1") is True
        report["checks"]["not_newer"] = mod.is_newer_version("3.13.1", "3.13.1") is False
        report["checks"]["checksum_parse"] = mod.parse_sha256_checksum("a" * 64 + "  Deimos.exe\n") == "a" * 64
        sample = Path(tempfile.mkdtemp()) / "sample.bin"
        sample.write_bytes(b"deimos")
        report["checks"]["sha256_file"] = mod.sha256_file(sample) == "44bb41f280055f5a73c6441bbbd5cda7d2d75245a9661f9926a90d3591f0c6e2"
        bad_release = mod.ReleaseInfo("v3.14.0", None, None, False, False, {}, {})
        warnings = mod.validate_release_assets(bad_release)
        report["checks"]["missing_assets_warn"] = any("Deimos.exe" in w for w in warnings)
    except Exception as exc:
        report["blockers"].append(str(exc))
    for name, ok in report["checks"].items():
        if not ok:
            report["blockers"].append(f"smoke check failed: {name}")
    report["passed"] = not report["blockers"]
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else ".", sys.argv[2] if len(sys.argv) > 2 else ".codex/reports/update-system-smoke.json"))
