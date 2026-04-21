"""Build and format a report of path alias resolutions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from vaultpull.path_alias import AliasConfig, resolve_key


@dataclass
class AliasReport:
    environment: str
    mappings: List[Tuple[str, str, str]] = field(default_factory=list)  # (vault_path, original_key, resolved_key)

    @property
    def total(self) -> int:
        return len(self.mappings)

    @property
    def renamed(self) -> int:
        return sum(1 for _, orig, resolved in self.mappings if orig != resolved)


def build_alias_report(
    path_secrets: Dict[str, Dict[str, str]],
    cfg: AliasConfig,
    environment: str = "default",
) -> AliasReport:
    """Produce an AliasReport for all secrets across multiple vault paths."""
    report = AliasReport(environment=environment)
    for vault_path, secrets in path_secrets.items():
        for key in secrets:
            resolved = resolve_key(vault_path, key, cfg)
            report.mappings.append((vault_path, key, resolved))
    return report


def format_alias_report(report: AliasReport) -> str:
    """Return a human-readable summary of alias resolutions."""
    lines: List[str] = [
        f"Alias Report  [env: {report.environment}]",
        f"  Total keys : {report.total}",
        f"  Renamed    : {report.renamed}",
        "",
    ]
    if report.mappings:
        lines.append(f"  {'VAULT PATH':<30} {'ORIGINAL KEY':<25} {'RESOLVED KEY'}")
        lines.append("  " + "-" * 75)
        for vault_path, orig, resolved in report.mappings:
            marker = "*" if orig != resolved else " "
            lines.append(f"{marker} {vault_path:<30} {orig:<25} {resolved}")
    else:
        lines.append("  (no keys)")
    return "\n".join(lines)
