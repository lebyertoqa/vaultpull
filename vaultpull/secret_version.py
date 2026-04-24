"""Track and compare Vault secret versions."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass
class VersionRecord:
    path: str
    version: int
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class VersionReport:
    environment: str
    records: Dict[str, VersionRecord] = field(default_factory=dict)
    upgraded: list = field(default_factory=list)
    unchanged: list = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.records)


def _version_file(base_dir: str, environment: str) -> Path:
    return Path(base_dir) / f".vaultpull_versions_{environment}.json"


def load_versions(base_dir: str, environment: str) -> Dict[str, int]:
    """Load previously recorded secret versions from disk."""
    vfile = _version_file(base_dir, environment)
    if not vfile.exists():
        return {}
    try:
        data = json.loads(vfile.read_text())
        return {k: int(v) for k, v in data.items()}
    except (json.JSONDecodeError, ValueError):
        return {}


def save_versions(base_dir: str, environment: str, versions: Dict[str, int]) -> None:
    """Persist secret versions to disk."""
    vfile = _version_file(base_dir, environment)
    vfile.parent.mkdir(parents=True, exist_ok=True)
    vfile.write_text(json.dumps(versions, indent=2))


def build_version_report(
    environment: str,
    fetched: Dict[str, int],
    previous: Dict[str, int],
) -> VersionReport:
    """Compare fetched versions against previously saved ones."""
    report = VersionReport(environment=environment)
    for path, version in fetched.items():
        record = VersionRecord(path=path, version=version)
        report.records[path] = record
        if previous.get(path, -1) < version:
            report.upgraded.append(path)
        else:
            report.unchanged.append(path)
    return report


def format_version_report(report: VersionReport) -> str:
    """Return a human-readable summary of version changes."""
    lines = [f"Secret version report [{report.environment}]"]
    lines.append(f"  Total paths : {report.total}")
    lines.append(f"  Upgraded    : {len(report.upgraded)}")
    lines.append(f"  Unchanged   : {len(report.unchanged)}")
    if report.upgraded:
        lines.append("  Upgraded paths:")
        for p in sorted(report.upgraded):
            lines.append(f"    + {p} (v{report.records[p].version})")
    return "\n".join(lines)
