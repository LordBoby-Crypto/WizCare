"""Verified Wizard101 knowledge catalog helpers for Deimos/WizCare.

This module is intentionally conservative: it loads local fact records and reports
coverage gaps instead of guessing. Auto-combat and bot features can use this as a
safe bridge from raw game state to source-linked Wizard101 facts.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable


CATALOG_SCHEMA_VERSION = "wizard101-knowledge-v1"
VERIFICATION_ORDER = {
    "unverified": 0,
    "source-linked": 1,
    "exact-page-verified": 2,
    "strategy-reviewed": 3,
}


@dataclass(frozen=True)
class KnowledgeIssue:
    dataset: str
    record_id: str
    message: str


@dataclass(frozen=True)
class KnowledgeRecord:
    dataset: str
    data: dict[str, Any]

    @property
    def id(self) -> str:
        return str(self.data.get("id") or "")

    @property
    def name(self) -> str:
        return str(self.data.get("name") or "")

    @property
    def verification_level(self) -> str:
        verification = self.data.get("verification") or {}
        return str(verification.get("level") or "unverified")

    def is_at_least(self, level: str) -> bool:
        return VERIFICATION_ORDER.get(self.verification_level, -1) >= VERIFICATION_ORDER[level]


class Wizard101KnowledgeCatalog:
    """Read-only local catalog of verified Wizard101 facts."""

    def __init__(self, root: Path | str | None = None):
        self.root = Path(root) if root is not None else Path(__file__).resolve().parents[1]
        self.manifest_path = self.root / "data" / "wizard101" / "catalog_manifest.json"
        self.manifest = self._load_manifest()
        self.records: dict[str, list[KnowledgeRecord]] = {}
        self.issues: list[KnowledgeIssue] = []
        self._load_all()

    def _load_manifest(self) -> dict[str, Any]:
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        if manifest.get("schema_version") != CATALOG_SCHEMA_VERSION:
            raise ValueError(f"Unsupported Wizard101 catalog schema: {manifest.get('schema_version')}")
        return manifest

    def _load_jsonl(self, dataset: str, path: Path, required_fields: Iterable[str]) -> list[KnowledgeRecord]:
        records: list[KnowledgeRecord] = []
        if not path.exists():
            self.issues.append(KnowledgeIssue(dataset, "", f"missing dataset file: {path}"))
            return records
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            data = json.loads(line)
            record = KnowledgeRecord(dataset=dataset, data=data)
            for field in required_fields:
                if field not in data:
                    self.issues.append(KnowledgeIssue(dataset, record.id or f"line:{line_number}", f"missing required field: {field}"))
            level = record.verification_level
            if level not in VERIFICATION_ORDER:
                self.issues.append(KnowledgeIssue(dataset, record.id or f"line:{line_number}", f"unknown verification level: {level}"))
            records.append(record)
        return records

    def _load_all(self) -> None:
        datasets = self.manifest.get("datasets") or {}
        for dataset, meta in datasets.items():
            path = self.root / str(meta["path"])
            required_fields = list(meta.get("required_fields") or [])
            self.records[dataset] = self._load_jsonl(dataset, path, required_fields)

    def dataset_counts(self) -> dict[str, int]:
        return {dataset: len(records) for dataset, records in sorted(self.records.items())}

    def dataset_completion_status(self) -> dict[str, dict[str, Any]]:
        targets = self.manifest.get("coverage_targets") or {}
        status: dict[str, dict[str, Any]] = {}
        for dataset, records in sorted(self.records.items()):
            target = targets.get(dataset) or {}
            minimum = str(target.get("minimum_verification") or "exact-page-verified")
            verified_records = [record for record in records if record.is_at_least(minimum)]
            status[dataset] = {
                "records": len(records),
                "minimum_verification": minimum,
                "verified_records": len(verified_records),
                "required_for_complete_project": bool(target.get("required_for_complete_project", True)),
                "complete": bool(records) and len(verified_records) == len(records),
            }
        return status

    def find_by_name(self, dataset: str, name: str) -> list[KnowledgeRecord]:
        needle = name.casefold().strip()
        return [record for record in self.records.get(dataset, []) if record.name.casefold() == needle]

    def get_enemy_combat_context(self, enemy_name: str) -> dict[str, Any]:
        """Return enemy facts safe for auto-combat planning.

        If the enemy is unknown or not exact-page verified, callers should use a
        generic safe combat config rather than enemy-specific strategy.
        """
        matches = self.find_by_name("enemies", enemy_name)
        if not matches:
            return {
                "enemy_name": enemy_name,
                "known": False,
                "strategy_unlocked": False,
                "reason": "enemy is not present in the verified Wizard101 catalog",
            }
        best = max(matches, key=lambda record: VERIFICATION_ORDER.get(record.verification_level, -1))
        combat = best.data.get("combat") or {}
        strategy_unlocked = best.is_at_least("strategy-reviewed")
        return {
            "enemy_name": best.name,
            "known": True,
            "record_id": best.id,
            "verification_level": best.verification_level,
            "strategy_unlocked": strategy_unlocked,
            "school": combat.get("school"),
            "health": combat.get("health"),
            "resists": combat.get("resists") or {},
            "boosts": combat.get("boosts") or {},
            "cheats": combat.get("cheats") or [],
            "recommended_policy": "enemy-specific" if strategy_unlocked else "generic-safe",
        }

    def coverage_report(self) -> dict[str, Any]:
        counts = self.dataset_counts()
        dataset_status = self.dataset_completion_status()
        required_datasets_complete = all(
            item["complete"] for item in dataset_status.values() if item["required_for_complete_project"]
        )
        complete = bool(counts) and required_datasets_complete and not self.issues
        missing_datasets = [dataset for dataset, count in counts.items() if count == 0]
        return {
            "schema_version": self.manifest.get("schema_version"),
            "counts": counts,
            "dataset_status": dataset_status,
            "missing_datasets": missing_datasets,
            "total_records": sum(counts.values()),
            "issues": [issue.__dict__ for issue in self.issues],
            "complete": complete,
            "completion_note": "The framework is ready, but the game-wide fact import is not complete until every required dataset is populated and verified to its required level.",
        }


def load_default_catalog() -> Wizard101KnowledgeCatalog:
    return Wizard101KnowledgeCatalog()
