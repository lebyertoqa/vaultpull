"""Track and validate dependencies between secrets."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


def _split_csv(value: str) -> List[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass
class DependencyConfig:
    """Configuration for secret dependency rules."""
    requires: Dict[str, List[str]] = field(default_factory=dict)  # key -> [required keys]
    conflicts: Dict[str, List[str]] = field(default_factory=dict)  # key -> [conflicting keys]
    groups: Dict[str, List[str]] = field(default_factory=dict)    # group_name -> [keys]
    strict: bool = False


def load_dependency_config(section: Optional[dict] = None) -> DependencyConfig:
    """Load dependency config from an optional config dict section."""
    cfg = section or {}
    requires: Dict[str, List[str]] = {}
    conflicts: Dict[str, List[str]] = {}
    groups: Dict[str, List[str]] = {}

    for key, value in cfg.items():
        if key.startswith("requires."):
            secret_key = key[len("requires."):]
            requires[secret_key] = _split_csv(value)
        elif key.startswith("conflicts."):
            secret_key = key[len("conflicts."):]
            conflicts[secret_key] = _split_csv(value)
        elif key.startswith("group."):
            group_name = key[len("group."):]
            groups[group_name] = _split_csv(value)

    strict = str(cfg.get("strict", "false")).lower() == "true"
    return DependencyConfig(requires=requires, conflicts=conflicts, groups=groups, strict=strict)


@dataclass
class DependencyViolation:
    key: str
    kind: str  # "missing_dependency" | "conflict" | "incomplete_group"
    detail: str


@dataclass
class DependencyReport:
    violations: List[DependencyViolation] = field(default_factory=list)
    checked_keys: int = 0

    @property
    def has_violations(self) -> bool:
        return len(self.violations) > 0


def check_dependencies(secrets: Dict[str, str], config: DependencyConfig) -> DependencyReport:
    """Validate secrets against dependency rules."""
    present: Set[str] = set(secrets.keys())
    violations: List[DependencyViolation] = []

    for key, deps in config.requires.items():
        if key in present:
            for dep in deps:
                if dep not in present:
                    violations.append(DependencyViolation(
                        key=key,
                        kind="missing_dependency",
                        detail=f"'{key}' requires '{dep}' which is not present",
                    ))

    for key, conflicting in config.conflicts.items():
        if key in present:
            for other in conflicting:
                if other in present:
                    violations.append(DependencyViolation(
                        key=key,
                        kind="conflict",
                        detail=f"'{key}' conflicts with '{other}'",
                    ))

    for group_name, members in config.groups.items():
        found = [m for m in members if m in present]
        if found and len(found) < len(members):
            missing = [m for m in members if m not in present]
            violations.append(DependencyViolation(
                key=group_name,
                kind="incomplete_group",
                detail=f"Group '{group_name}' is incomplete; missing: {', '.join(missing)}",
            ))

    return DependencyReport(violations=violations, checked_keys=len(present))
