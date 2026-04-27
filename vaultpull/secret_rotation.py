"""Tracks secret rotation status and flags stale secrets."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RotationRecord:
    key: str
    last_rotated: str          # ISO-8601 timestamp
    rotation_interval_days: int
    environment: str = "default"

    def days_since_rotation(self) -> float:
        last = datetime.fromisoformat(self.last_rotated)
        now = datetime.now(timezone.utc)
        return (now - last).total_seconds() / 86400

    def is_stale(self) -> bool:
        return self.days_since_rotation() >= self.rotation_interval_days

    def days_until_due(self) -> float:
        return self.rotation_interval_days - self.days_since_rotation()

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "RotationRecord":
        return RotationRecord(
            key=d["key"],
            last_rotated=d["last_rotated"],
            rotation_interval_days=int(d["rotation_interval_days"]),
            environment=d.get("environment", "default"),
        )


def _rotation_file(base_dir: Path, environment: str) -> Path:
    return base_dir / f".vaultpull_rotation_{environment}.json"


def load_rotation_records(base_dir: Path, environment: str = "default") -> Dict[str, RotationRecord]:
    path = _rotation_file(base_dir, environment)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        return {k: RotationRecord.from_dict(v) for k, v in data.items()}
    except (json.JSONDecodeError, KeyError):
        return {}


def save_rotation_records(records: Dict[str, RotationRecord], base_dir: Path, environment: str = "default") -> None:
    path = _rotation_file(base_dir, environment)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({k: v.to_dict() for k, v in records.items()}, indent=2))


def mark_rotated(key: str, base_dir: Path, interval_days: int = 90, environment: str = "default") -> RotationRecord:
    records = load_rotation_records(base_dir, environment)
    record = RotationRecord(
        key=key,
        last_rotated=_now_iso(),
        rotation_interval_days=interval_days,
        environment=environment,
    )
    records[key] = record
    save_rotation_records(records, base_dir, environment)
    return record


def get_stale_secrets(secrets: Dict[str, str], base_dir: Path, interval_days: int = 90, environment: str = "default") -> List[RotationRecord]:
    records = load_rotation_records(base_dir, environment)
    stale: List[RotationRecord] = []
    for key in secrets:
        if key in records:
            if records[key].is_stale():
                stale.append(records[key])
        else:
            # Never recorded — treat as immediately stale
            stale.append(RotationRecord(
                key=key,
                last_rotated="1970-01-01T00:00:00+00:00",
                rotation_interval_days=interval_days,
                environment=environment,
            ))
    return stale
