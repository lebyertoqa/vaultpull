"""Report on how Vault secret keys were mapped to env var names."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from vaultpull.secret_env_map import EnvMapConfig, apply_env_prefix


@dataclass
class EnvMapReport:
    environment: str
    path: str
    mappings: List[Dict[str, str]] = field(default_factory=list)  # [{original, mapped}]

    @property
    def total(self) -> int:
        return len(self.mappings)

    @property
    def renamed(self) -> int:
        return sum(1 for m in self.mappings if m["original"] != m["mapped"])


def build_env_map_report(
    secrets: Dict[str, str],
    path: str,
    cfg: EnvMapConfig,
    environment: str = "default",
) -> EnvMapReport:
    """Build a report showing original vs mapped key names."""
    mappings = [
        {"original": k, "mapped": apply_env_prefix(k, path, cfg)}
        for k in secrets
    ]
    return EnvMapReport(environment=environment, path=path, mappings=mappings)


def format_env_map_report(report: EnvMapReport) -> str:
    """Return a human-readable summary of the env-map report."""
    lines: List[str] = [
        f"Env Map Report [{report.environment}] path={report.path}",
        f"  Total keys : {report.total}",
        f"  Renamed    : {report.renamed}",
    ]
    if report.mappings:
        lines.append("  Key mappings:")
        for m in report.mappings:
            arrow = "->" if m["original"] != m["mapped"] else "=="
            lines.append(f"    {m['original']} {arrow} {m['mapped']}")
    return "\n".join(lines)
