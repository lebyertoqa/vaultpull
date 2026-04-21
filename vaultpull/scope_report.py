"""Generate a human-readable report of scope filtering decisions."""

from __future__ import annotations

from typing import Dict, List, Tuple

from vaultpull.secret_scope import ScopeConfig, is_path_allowed


@dataclass_like = None  # avoid import side-effects; use plain class


class ScopeReport:
    def __init__(
        self,
        environment: str,
        allowed: List[str],
        denied: List[str],
        skipped: List[str],
    ) -> None:
        self.environment = environment
        self.allowed = allowed
        self.denied = denied
        self.skipped = skipped

    @property
    def total(self) -> int:
        return len(self.allowed) + len(self.denied) + len(self.skipped)


def build_scope_report(paths: List[str], scope: ScopeConfig) -> ScopeReport:
    """Classify each path as allowed, denied, or skipped (strict + no allow-list)."""
    allowed: List[str] = []
    denied: List[str] = []
    skipped: List[str] = []

    for path in paths:
        if is_path_allowed(path, scope):
            allowed.append(path)
        elif scope.strict and not scope.allowed_paths:
            skipped.append(path)
        else:
            denied.append(path)

    return ScopeReport(
        environment=scope.environment,
        allowed=allowed,
        denied=denied,
        skipped=skipped,
    )


def format_scope_report(report: ScopeReport) -> str:
    """Return a plain-text summary of scope filtering results."""
    lines = [
        f"Scope report — environment: {report.environment}",
        f"  Allowed : {len(report.allowed)}",
        f"  Denied  : {len(report.denied)}",
        f"  Skipped : {len(report.skipped)}",
        f"  Total   : {report.total}",
    ]
    if report.denied:
        lines.append("  Denied paths:")
        for p in report.denied:
            lines.append(f"    - {p}")
    if report.skipped:
        lines.append("  Skipped paths (strict mode, no allow-list):")
        for p in report.skipped:
            lines.append(f"    - {p}")
    return "\n".join(lines)
