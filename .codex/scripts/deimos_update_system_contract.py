from __future__ import annotations
import ast, json, sys
from pathlib import Path

REQUIRED_CONSTANTS = {
    "STABLE_EXE_ASSET": "Deimos.exe",
    "STABLE_CHECKSUM_ASSET": "Deimos.exe.sha256",
    "STABLE_MANIFEST_ASSET": "release-manifest.json",
}
REQUIRED_FUNCTIONS = {
    "check_for_update",
    "validate_release_assets",
    "stage_release_assets",
    "parse_sha256_checksum",
    "sha256_file",
    "download_asset",
}

def main(repo_root: str, out_path: str) -> int:
    root = Path(repo_root)
    target = root / "src" / "update_system.py"
    report = {"target": str(target), "blockers": [], "warnings": [], "constants": {}, "functions": []}
    if not target.exists():
        report["blockers"].append("src/update_system.py is missing")
    else:
        tree = ast.parse(target.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id in REQUIRED_CONSTANTS:
                        report["constants"][t.id] = ast.literal_eval(node.value)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                report["functions"].append(node.name)
        for name, expected in REQUIRED_CONSTANTS.items():
            if report["constants"].get(name) != expected:
                report["blockers"].append(f"{name} must be {expected!r}")
        missing = sorted(REQUIRED_FUNCTIONS - set(report["functions"]))
        if missing:
            report["blockers"].append(f"missing update-system functions: {', '.join(missing)}")
        text = target.read_text(encoding="utf-8")
        forbidden = ["os.replace(", "shutil.move(", "subprocess.Popen(", "subprocess.run("]
        used = [f for f in forbidden if f in text]
        if used:
            report["blockers"].append("review-first updater must not install/relaunch automatically: " + ", ".join(used))
    report["passed"] = not report["blockers"]
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else ".", sys.argv[2] if len(sys.argv) > 2 else ".codex/reports/update-system-contract.json"))
