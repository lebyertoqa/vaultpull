"""Build and format a human-readable snapshot comparison report."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from vaultpull.secret_snapshot import Snapshot, snapshots_differ


@dataclass
class SnapshotReport:
    environment: str
    previous: Optional[Snapshot]
    current: Snapshot
    added_keys: List[str] = field(default_factory=list)
    removed_keys: List[str] = field(default_factory=list)
    changed: bool = False

    @property
    def total_keys(self) -> int:
        return len(self.current.keys)


def build_snapshot_report(
    previous: Optional[Snapshot],
    current: Snapshot,
) -> SnapshotReport:
    """Compare *previous* and *current* snapshots and return a report."""
    prev_keys = set(previous.keys) if previous else set()
    curr_keys = set(current.keys)

    added = sorted(curr_keys - prev_keys)
    removed = sorted(prev_keys - curr_keys)
    changed = snapshots_differ(previous, current)

    return SnapshotReport(
        environment=current.environment,
        previous=previous,
        current=current,
        added_keys=added,
        removed_keys=removed,
        changed=changed,
    )


def format_snapshot_report(report: SnapshotReport) -> str:
    """Return a plain-text summary of the snapshot report."""
    lines: List[str] = [
        f"Snapshot report  [{report.environment}]",
        f"  Captured : {report.current.captured_at}",
        f"  Total keys: {report.total_keys}",
        f"  Changed  : {report.changed}",
    ]
    if report.added_keys:
        lines.append(f"  Added ({len(report.added_keys)}): {', '.join(report.added_keys)}")
    if report.removed_keys:
        lines.append(f"  Removed ({len(report.removed_keys)}): {', '.join(report.removed_keys)}")
    if not report.changed:
        lines.append("  No changes detected since last snapshot.")
    return "\n".join(lines)
