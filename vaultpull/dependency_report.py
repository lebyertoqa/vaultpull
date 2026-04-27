"""Format and summarise dependency check reports."""
from __future__ import annotations

from typing import Optional

from vaultpull.secret_dependencies import DependencyConfig, DependencyReport, check_dependencies


def build_dependency_report(
    secrets: dict,
    config: DependencyConfig,
    environment: str = "default",
) -> dict:
    """Run dependency checks and return a structured report dict."""
    report: DependencyReport = check_dependencies(secrets, config)
    return {
        "environment": environment,
        "checked_keys": report.checked_keys,
        "violation_count": len(report.violations),
        "has_violations": report.has_violations,
        "violations": [
            {"key": v.key, "kind": v.kind, "detail": v.detail}
            for v in report.violations
        ],
    }


def format_dependency_report(
    report: dict,
    verbose: bool = False,
) -> str:
    """Render a dependency report as a human-readable string."""
    lines = [
        f"Dependency check — environment: {report['environment']}",
        f"  Keys checked : {report['checked_keys']}",
        f"  Violations   : {report['violation_count']}",
    ]

    if report["has_violations"]:
        lines.append("")
        lines.append("  Violations:")
        for v in report["violations"]:
            prefix = "    [" + v["kind"] + "]"
            lines.append(f"{prefix} {v['detail']}")
    elif verbose:
        lines.append("  All dependency rules satisfied.")

    return "\n".join(lines)


def describe_dependencies(config: DependencyConfig) -> str:
    """Return a short human-readable summary of the dependency config."""
    parts = []
    if config.requires:
        parts.append(f"{len(config.requires)} require rule(s)")
    if config.conflicts:
        parts.append(f"{len(config.conflicts)} conflict rule(s)")
    if config.groups:
        parts.append(f"{len(config.groups)} group(s)")
    if not parts:
        return "no dependency rules configured"
    suffix = " [strict]" if config.strict else ""
    return ", ".join(parts) + suffix
