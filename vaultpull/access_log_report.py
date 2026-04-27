"""Build and format human-readable reports from the secret access log."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from vaultpull.secret_access_log import AccessLog, AccessRecord


@dataclass
class AccessLogReport:
    environment: str
    total: int
    cached: int
    live: int
    by_path: Dict[str, int]
    records: List[AccessRecord]


def build_access_log_report(log: AccessLog) -> AccessLogReport:
    """Summarise an AccessLog into a structured report."""
    by_path: Dict[str, int] = {}
    for record in log.records:
        by_path[record.path] = by_path.get(record.path, 0) + 1

    cached = log.cached_count
    return AccessLogReport(
        environment=log.environment,
        total=log.total,
        cached=cached,
        live=log.total - cached,
        by_path=by_path,
        records=log.records,
    )


def format_access_log_report(report: AccessLogReport) -> str:
    """Return a plain-text summary of the access log report."""
    lines: List[str] = [
        f"Secret Access Log — {report.environment}",
        f"  Total keys accessed : {report.total}",
        f"  From cache          : {report.cached}",
        f"  Live from Vault     : {report.live}",
    ]
    if report.by_path:
        lines.append("  Paths accessed:")
        for path, count in sorted(report.by_path.items()):
            lines.append(f"    {path}: {count} key(s)")
    if not report.records:
        lines.append("  (no access records)")
    return "\n".join(lines)
