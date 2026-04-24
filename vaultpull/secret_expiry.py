"""Track and report secret expiry/TTL metadata from Vault."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class ExpiryConfig:
    warn_before_days: int = 7
    fail_on_expired: bool = False
    enabled: bool = True


def load_expiry_config(section: Optional[Dict] = None) -> ExpiryConfig:
    """Load expiry config from dict section, falling back to env vars."""
    s = section or {}
    warn = int(s.get("warn_before_days") or os.getenv("VAULTPULL_EXPIRY_WARN_DAYS", "7"))
    fail = str(s.get("fail_on_expired") or os.getenv("VAULTPULL_EXPIRY_FAIL", "false")).lower() == "true"
    enabled = str(s.get("enabled") or os.getenv("VAULTPULL_EXPIRY_ENABLED", "true")).lower() == "true"
    return ExpiryConfig(warn_before_days=warn, fail_on_expired=fail, enabled=enabled)


@dataclass
class ExpiryRecord:
    key: str
    expires_at: Optional[datetime]
    ttl_seconds: Optional[int]

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) >= self.expires_at

    def days_until_expiry(self) -> Optional[float]:
        if self.expires_at is None:
            return None
        delta = self.expires_at - datetime.now(timezone.utc)
        return delta.total_seconds() / 86400


@dataclass
class ExpiryReport:
    environment: str
    records: List[ExpiryRecord] = field(default_factory=list)
    expired: List[str] = field(default_factory=list)
    expiring_soon: List[str] = field(default_factory=list)


def build_expiry_report(
    environment: str,
    records: List[ExpiryRecord],
    config: ExpiryConfig,
) -> ExpiryReport:
    """Classify records into expired / expiring-soon buckets."""
    expired: List[str] = []
    expiring_soon: List[str] = []
    for rec in records:
        if rec.is_expired:
            expired.append(rec.key)
        else:
            days = rec.days_until_expiry()
            if days is not None and days <= config.warn_before_days:
                expiring_soon.append(rec.key)
    return ExpiryReport(
        environment=environment,
        records=records,
        expired=expired,
        expiring_soon=expiring_soon,
    )


def format_expiry_report(report: ExpiryReport) -> str:
    lines = [f"Expiry Report [{report.environment}]"]
    lines.append(f"  Total tracked : {len(report.records)}")
    lines.append(f"  Expired       : {len(report.expired)}")
    lines.append(f"  Expiring soon : {len(report.expiring_soon)}")
    for key in report.expired:
        lines.append(f"    [EXPIRED]  {key}")
    for key in report.expiring_soon:
        lines.append(f"    [WARNING]  {key}")
    return "\n".join(lines)
