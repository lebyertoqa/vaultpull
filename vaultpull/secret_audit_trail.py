"""Audit trail: record and query per-secret access and mutation events."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TrailEntry:
    key: str
    event: str          # "fetched" | "written" | "skipped" | "rotated"
    environment: str
    timestamp: str
    source_path: str
    changed: bool = False
    actor: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "TrailEntry":
        return cls(
            key=data["key"],
            event=data["event"],
            environment=data["environment"],
            timestamp=data["timestamp"],
            source_path=data["source_path"],
            changed=data.get("changed", False),
            actor=data.get("actor"),
        )


def _trail_file(base_dir: Path, environment: str) -> Path:
    return base_dir / f"audit_trail_{environment}.jsonl"


def append_trail_entries(entries: List[TrailEntry], base_dir: Path) -> None:
    """Append trail entries to the per-environment JSONL file."""
    if not entries:
        return
    env = entries[0].environment
    trail_path = _trail_file(base_dir, env)
    trail_path.parent.mkdir(parents=True, exist_ok=True)
    with trail_path.open("a", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(json.dumps(entry.to_dict()) + "\n")


def read_trail(base_dir: Path, environment: str) -> List[TrailEntry]:
    """Read all trail entries for an environment."""
    trail_path = _trail_file(base_dir, environment)
    if not trail_path.exists():
        return []
    entries: List[TrailEntry] = []
    with trail_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    entries.append(TrailEntry.from_dict(json.loads(line)))
                except (KeyError, json.JSONDecodeError):
                    continue
    return entries


def build_trail_entries(
    secrets: dict,
    changed_keys: set,
    skipped_keys: set,
    environment: str,
    source_path: str,
    actor: Optional[str] = None,
) -> List[TrailEntry]:
    """Create trail entries for a sync run."""
    now = _now_iso()
    entries = []
    for key in secrets:
        if key in skipped_keys:
            event = "skipped"
        elif key in changed_keys:
            event = "written"
        else:
            event = "fetched"
        entries.append(TrailEntry(
            key=key,
            event=event,
            environment=environment,
            timestamp=now,
            source_path=source_path,
            changed=(key in changed_keys),
            actor=actor or os.environ.get("VAULTPULL_ACTOR"),
        ))
    return entries
