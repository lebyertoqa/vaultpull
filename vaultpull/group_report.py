"""Build and format a report of how secrets were grouped."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from vaultpull.secret_group import GroupConfig, group_secrets


@dataclass
class GroupReport:
    environment: str
    groups: Dict[str, List[str]] = field(default_factory=dict)  # group -> key list
    ungrouped: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return sum(len(v) for v in self.groups.values()) + len(self.ungrouped)

    @property
    def group_count(self) -> int:
        return len(self.groups)


def build_group_report(
    secrets: Dict[str, str],
    cfg: GroupConfig,
    environment: str = "default",
) -> GroupReport:
    """Produce a GroupReport from a flat secrets dict."""
    partitioned = group_secrets(secrets, cfg)
    groups: Dict[str, List[str]] = {}
    ungrouped: List[str] = []

    for group_name, group_secrets_map in partitioned.items():
        if group_name == cfg.default_group and not cfg.group_by_prefix:
            ungrouped.extend(group_secrets_map.keys())
        else:
            groups[group_name] = sorted(group_secrets_map.keys())

    return GroupReport(environment=environment, groups=groups, ungrouped=sorted(ungrouped))


def format_group_report(report: GroupReport) -> str:
    """Return a human-readable summary of the group report."""
    lines: List[str] = [
        f"Secret Group Report [{report.environment}]",
        f"  Total secrets : {report.total}",
        f"  Groups found  : {report.group_count}",
        "",
    ]
    for group_name, keys in sorted(report.groups.items()):
        lines.append(f"  [{group_name}] ({len(keys)} keys)")
        for k in keys:
            lines.append(f"    - {k}")
    if report.ungrouped:
        lines.append(f"  [ungrouped] ({len(report.ungrouped)} keys)")
        for k in report.ungrouped:
            lines.append(f"    - {k}")
    return "\n".join(lines)
