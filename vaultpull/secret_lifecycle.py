"""Secret lifecycle management.

Tracks the full lifecycle state of each secret: when it was first seen,
last synced, last rotated, expiry status, and staleness. Provides a
unified view across rotation, TTL, expiry, and version records.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from vaultpull.secret_rotation import RotationRecord, load_rotation_records
from vaultpull.secret_ttl import TtlRecord, load_ttl_records
from vaultpull.secret_expiry import ExpiryRecord, is_expired as expiry_is_expired
from vaultpull.secret_version import VersionRecord, load_versions


@dataclass
class LifecycleState:
    """Unified lifecycle state for a single secret key."""

    key: str
    first_seen: Optional[str] = None
    last_synced: Optional[str] = None
    # Rotation
    rotation_due: bool = False
    days_since_rotation: Optional[int] = None
    # TTL
    ttl_expired: bool = False
    ttl_seconds_remaining: Optional[int] = None
    # Expiry
    expiry_expired: bool = False
    days_until_expiry: Optional[int] = None
    # Version
    current_version: Optional[int] = None
    version_changed: bool = False
    # Overall health
    healthy: bool = True
    issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "key": self.key,
            "first_seen": self.first_seen,
            "last_synced": self.last_synced,
            "rotation_due": self.rotation_due,
            "days_since_rotation": self.days_since_rotation,
            "ttl_expired": self.ttl_expired,
            "ttl_seconds_remaining": self.ttl_seconds_remaining,
            "expiry_expired": self.expiry_expired,
            "days_until_expiry": self.days_until_expiry,
            "current_version": self.current_version,
            "version_changed": self.version_changed,
            "healthy": self.healthy,
            "issues": self.issues,
        }


@dataclass
class LifecycleReport:
    """Aggregated lifecycle report across all tracked secrets."""

    environment: str
    states: List[LifecycleState] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.states)

    @property
    def unhealthy(self) -> List[LifecycleState]:
        return [s for s in self.states if not s.healthy]

    @property
    def healthy(self) -> List[LifecycleState]:
        return [s for s in self.states if s.healthy]


def build_lifecycle_report(
    secrets: Dict[str, str],
    *,
    rotation_records: Optional[Dict[str, RotationRecord]] = None,
    ttl_records: Optional[Dict[str, TtlRecord]] = None,
    expiry_records: Optional[Dict[str, ExpiryRecord]] = None,
    version_records: Optional[Dict[str, VersionRecord]] = None,
    environment: str = "default",
) -> LifecycleReport:
    """Build a lifecycle report for the given secrets dict.

    Each optional record dict maps secret key -> record object.
    Pass None (or omit) for any record type not being tracked.
    """
    rotation_records = rotation_records or {}
    ttl_records = ttl_records or {}
    expiry_records = expiry_records or {}
    version_records = version_records or {}

    report = LifecycleReport(environment=environment)

    for key in secrets:
        state = LifecycleState(key=key)

        # --- Rotation ---
        rot = rotation_records.get(key)
        if rot is not None:
            state.days_since_rotation = rot.days_since_rotation
            state.rotation_due = rot.is_stale
            if rot.is_stale:
                state.issues.append(
                    f"rotation overdue ({rot.days_since_rotation}d since last rotation)"
                )

        # --- TTL ---
        ttl = ttl_records.get(key)
        if ttl is not None:
            state.ttl_expired = ttl.is_expired
            state.ttl_seconds_remaining = max(0, ttl.seconds_remaining)
            if ttl.is_expired:
                state.issues.append("TTL expired")

        # --- Expiry ---
        exp = expiry_records.get(key)
        if exp is not None:
            state.expiry_expired = expiry_is_expired(exp)
            if hasattr(exp, "days_until_expiry"):
                state.days_until_expiry = exp.days_until_expiry
            if state.expiry_expired:
                state.issues.append("secret past expiry date")

        # --- Version ---
        ver = version_records.get(key)
        if ver is not None:
            state.current_version = ver.version
            state.version_changed = getattr(ver, "changed", False)
            state.first_seen = getattr(ver, "first_seen", None)
            state.last_synced = getattr(ver, "last_synced", None)
            if state.version_changed:
                state.issues.append("version changed since last sync")

        state.healthy = len(state.issues) == 0
        report.states.append(state)

    return report


def format_lifecycle_report(report: LifecycleReport) -> str:
    """Return a human-readable summary of the lifecycle report."""
    lines = [
        f"Lifecycle Report  [{report.environment}]",
        f"  Total secrets : {report.total}",
        f"  Healthy       : {len(report.healthy)}",
        f"  Unhealthy     : {len(report.unhealthy)}",
    ]
    if report.unhealthy:
        lines.append("  Issues:")
        for state in report.unhealthy:
            for issue in state.issues:
                lines.append(f"    [{state.key}] {issue}")
    return "\n".join(lines)
