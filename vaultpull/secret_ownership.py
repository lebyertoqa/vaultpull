"""Track ownership metadata for secrets (team, owner, contact)."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional


def _split_csv(value: str) -> List[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass
class OwnershipRecord:
    key: str
    owner: Optional[str] = None
    team: Optional[str] = None
    contact: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "OwnershipRecord":
        return cls(
            key=data["key"],
            owner=data.get("owner"),
            team=data.get("team"),
            contact=data.get("contact"),
        )


@dataclass
class OwnershipConfig:
    default_owner: Optional[str] = None
    default_team: Optional[str] = None
    default_contact: Optional[str] = None
    tracked_keys: List[str] = None

    def __post_init__(self):
        if self.tracked_keys is None:
            self.tracked_keys = []


def load_ownership_config(section: Optional[dict] = None) -> OwnershipConfig:
    sec = section or {}
    return OwnershipConfig(
        default_owner=sec.get("default_owner") or os.environ.get("VAULTPULL_OWNER"),
        default_team=sec.get("default_team") or os.environ.get("VAULTPULL_TEAM"),
        default_contact=sec.get("default_contact") or os.environ.get("VAULTPULL_CONTACT"),
        tracked_keys=_split_csv(sec.get("tracked_keys", os.environ.get("VAULTPULL_TRACKED_KEYS", ""))),
    )


def _ownership_file(base_dir: Path) -> Path:
    return base_dir / ".vaultpull" / "ownership.jsonl"


def load_ownership_records(base_dir: Path) -> Dict[str, OwnershipRecord]:
    path = _ownership_file(base_dir)
    if not path.exists():
        return {}
    records: Dict[str, OwnershipRecord] = {}
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = OwnershipRecord.from_dict(json.loads(line))
                records[rec.key] = rec
            except (KeyError, json.JSONDecodeError):
                continue
    return records


def save_ownership_records(base_dir: Path, records: Dict[str, OwnershipRecord]) -> None:
    path = _ownership_file(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        for rec in records.values():
            fh.write(json.dumps(rec.to_dict()) + "\n")


def assign_ownership(
    secrets: Dict[str, str],
    cfg: OwnershipConfig,
    existing: Optional[Dict[str, OwnershipRecord]] = None,
) -> Dict[str, OwnershipRecord]:
    result: Dict[str, OwnershipRecord] = dict(existing or {})
    keys = cfg.tracked_keys if cfg.tracked_keys else list(secrets.keys())
    for key in keys:
        if key not in secrets:
            continue
        if key not in result:
            result[key] = OwnershipRecord(
                key=key,
                owner=cfg.default_owner,
                team=cfg.default_team,
                contact=cfg.default_contact,
            )
    return result
