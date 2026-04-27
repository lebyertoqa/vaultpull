"""Track which secrets were accessed and when during a sync."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AccessRecord:
    key: str
    path: str
    accessed_at: str
    environment: str
    was_cached: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AccessRecord":
        return cls(
            key=data["key"],
            path=data["path"],
            accessed_at=data["accessed_at"],
            environment=data["environment"],
            was_cached=data.get("was_cached", False),
        )


@dataclass
class AccessLog:
    records: List[AccessRecord]
    synced_at: str
    environment: str

    @property
    def total(self) -> int:
        return len(self.records)

    @property
    def cached_count(self) -> int:
        return sum(1 for r in self.records if r.was_cached)


def _log_file(base_dir: Path, environment: str) -> Path:
    return base_dir / f".vaultpull_access_{environment}.jsonl"


def record_access(
    secrets: Dict[str, str],
    vault_path: str,
    environment: str,
    base_dir: Optional[Path] = None,
    was_cached: bool = False,
) -> AccessLog:
    """Record access for each secret key and persist to a JSONL log."""
    base_dir = base_dir or Path(os.getcwd())
    now = _now_iso()
    records = [
        AccessRecord(
            key=key,
            path=vault_path,
            accessed_at=now,
            environment=environment,
            was_cached=was_cached,
        )
        for key in secrets
    ]
    log_path = _log_file(base_dir, environment)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a") as fh:
        for record in records:
            fh.write(json.dumps(record.to_dict()) + "\n")
    return AccessLog(records=records, synced_at=now, environment=environment)


def load_access_log(
    environment: str,
    base_dir: Optional[Path] = None,
    limit: int = 200,
) -> List[AccessRecord]:
    """Read the most recent access records for an environment."""
    base_dir = base_dir or Path(os.getcwd())
    log_path = _log_file(base_dir, environment)
    if not log_path.exists():
        return []
    records: List[AccessRecord] = []
    with log_path.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    records.append(AccessRecord.from_dict(json.loads(line)))
                except (KeyError, json.JSONDecodeError):
                    continue
    return records[-limit:]
