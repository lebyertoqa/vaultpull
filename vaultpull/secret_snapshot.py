"""Snapshot support: capture and compare secret state at a point in time."""
from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fingerprint(secrets: Dict[str, str]) -> str:
    """Return a stable SHA-256 fingerprint of the secrets dict."""
    serialised = json.dumps(secrets, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialised.encode()).hexdigest()


@dataclass
class Snapshot:
    environment: str
    captured_at: str
    fingerprint: str
    keys: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "environment": self.environment,
            "captured_at": self.captured_at,
            "fingerprint": self.fingerprint,
            "keys": self.keys,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        return cls(
            environment=data["environment"],
            captured_at=data["captured_at"],
            fingerprint=data["fingerprint"],
            keys=data.get("keys", []),
        )


def _snapshot_path(base_dir: Path, environment: str) -> Path:
    return base_dir / f"{environment}.snapshot.json"


def capture_snapshot(
    secrets: Dict[str, str],
    environment: str,
    base_dir: Path,
) -> Snapshot:
    """Capture a snapshot of *secrets* and persist it to *base_dir*."""
    snap = Snapshot(
        environment=environment,
        captured_at=_now_iso(),
        fingerprint=_fingerprint(secrets),
        keys=sorted(secrets.keys()),
    )
    base_dir.mkdir(parents=True, exist_ok=True)
    _snapshot_path(base_dir, environment).write_text(
        json.dumps(snap.to_dict(), indent=2), encoding="utf-8"
    )
    return snap


def load_snapshot(environment: str, base_dir: Path) -> Optional[Snapshot]:
    """Load the most-recent snapshot for *environment*, or None."""
    path = _snapshot_path(base_dir, environment)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Snapshot.from_dict(data)
    except (json.JSONDecodeError, KeyError):
        return None


def snapshots_differ(a: Optional[Snapshot], b: Optional[Snapshot]) -> bool:
    """Return True when two snapshots have different fingerprints."""
    if a is None or b is None:
        return True
    return a.fingerprint != b.fingerprint
