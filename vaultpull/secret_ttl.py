"""TTL (time-to-live) tracking for fetched secrets."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional


_DEFAULT_TTL_SECONDS = 3600  # 1 hour


@dataclass
class TtlRecord:
    key: str
    fetched_at: float  # unix timestamp
    ttl_seconds: int

    @property
    def expires_at(self) -> float:
        return self.fetched_at + self.ttl_seconds

    @property
    def is_expired(self) -> bool:
        return time.time() >= self.expires_at

    @property
    def seconds_remaining(self) -> float:
        remaining = self.expires_at - time.time()
        return max(0.0, remaining)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "TtlRecord":
        return cls(
            key=data["key"],
            fetched_at=float(data["fetched_at"]),
            ttl_seconds=int(data["ttl_seconds"]),
        )


def _ttl_file(base_dir: Path) -> Path:
    return base_dir / ".vaultpull_ttl.json"


def load_ttl_records(base_dir: Path) -> Dict[str, TtlRecord]:
    """Load TTL records from disk; returns empty dict if missing or corrupt."""
    path = _ttl_file(base_dir)
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text())
        return {k: TtlRecord.from_dict(v) for k, v in raw.items()}
    except (json.JSONDecodeError, KeyError, ValueError):
        return {}


def save_ttl_records(base_dir: Path, records: Dict[str, TtlRecord]) -> None:
    """Persist TTL records to disk."""
    path = _ttl_file(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({k: v.to_dict() for k, v in records.items()}, indent=2))


def record_ttl(
    base_dir: Path,
    secrets: Dict[str, str],
    ttl_seconds: Optional[int] = None,
) -> Dict[str, TtlRecord]:
    """Create or refresh TTL records for the given secrets."""
    ttl = ttl_seconds if ttl_seconds is not None else int(
        os.environ.get("VAULTPULL_TTL_SECONDS", str(_DEFAULT_TTL_SECONDS))
    )
    now = time.time()
    existing = load_ttl_records(base_dir)
    for key in secrets:
        existing[key] = TtlRecord(key=key, fetched_at=now, ttl_seconds=ttl)
    save_ttl_records(base_dir, existing)
    return existing


def expired_keys(base_dir: Path) -> List[str]:
    """Return keys whose TTL has elapsed."""
    records = load_ttl_records(base_dir)
    return [k for k, r in records.items() if r.is_expired]
