"""Checksum tracking for vault secrets — detects tampering or unexpected changes."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


def _checksum(value: str) -> str:
    """Return a SHA-256 hex digest of the given string value."""
    return hashlib.sha256(value.encode()).hexdigest()


@dataclass
class ChecksumRecord:
    key: str
    digest: str
    algorithm: str = "sha256"

    def to_dict(self) -> dict:
        return {"key": self.key, "digest": self.digest, "algorithm": self.algorithm}

    @classmethod
    def from_dict(cls, data: dict) -> "ChecksumRecord":
        return cls(
            key=data["key"],
            digest=data["digest"],
            algorithm=data.get("algorithm", "sha256"),
        )


@dataclass
class ChecksumReport:
    environment: str
    records: Dict[str, ChecksumRecord] = field(default_factory=dict)
    tampered: list = field(default_factory=list)
    new_keys: list = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.records)

    @property
    def has_issues(self) -> bool:
        return bool(self.tampered)


def _checksum_file(base_dir: Path, environment: str) -> Path:
    return base_dir / f".vaultpull_checksums_{environment}.json"


def load_checksums(base_dir: Path, environment: str) -> Dict[str, ChecksumRecord]:
    path = _checksum_file(base_dir, environment)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        return {entry["key"]: ChecksumRecord.from_dict(entry) for entry in data}
    except (json.JSONDecodeError, KeyError):
        return {}


def save_checksums(
    base_dir: Path, environment: str, records: Dict[str, ChecksumRecord]
) -> None:
    path = _checksum_file(base_dir, environment)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([r.to_dict() for r in records.values()], indent=2))


def compute_checksums(secrets: Dict[str, str]) -> Dict[str, ChecksumRecord]:
    return {key: ChecksumRecord(key=key, digest=_checksum(value)) for key, value in secrets.items()}


def build_checksum_report(
    secrets: Dict[str, str],
    base_dir: Path,
    environment: str = "default",
) -> ChecksumReport:
    previous = load_checksums(base_dir, environment)
    current = compute_checksums(secrets)
    report = ChecksumReport(environment=environment, records=current)

    for key, record in current.items():
        if key not in previous:
            report.new_keys.append(key)
        elif previous[key].digest != record.digest:
            report.tampered.append(key)

    save_checksums(base_dir, environment, current)
    return report


def format_checksum_report(report: ChecksumReport) -> str:
    lines = [f"Checksum Report [{report.environment}]", f"  Total keys : {report.total}"]
    if report.new_keys:
        lines.append(f"  New keys   : {', '.join(sorted(report.new_keys))}")
    if report.tampered:
        lines.append(f"  Tampered   : {', '.join(sorted(report.tampered))}")
    if not report.has_issues:
        lines.append("  Status     : OK")
    return "\n".join(lines)
