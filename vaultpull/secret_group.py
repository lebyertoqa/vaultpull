"""Group secrets by namespace prefix or custom mapping."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


def _split_csv(value: str) -> List[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass
class GroupConfig:
    enabled: bool = False
    separator: str = "/"
    group_by_prefix: bool = True
    custom_groups: Dict[str, List[str]] = field(default_factory=dict)
    default_group: str = "default"


def load_group_config(section: Optional[Dict] = None) -> GroupConfig:
    """Load GroupConfig from an optional config dict, falling back to env vars."""
    s = section or {}

    enabled = s.get("enabled", os.environ.get("VAULTPULL_GROUP_ENABLED", "false")).lower() == "true"
    separator = s.get("separator", os.environ.get("VAULTPULL_GROUP_SEPARATOR", "/"))
    group_by_prefix = s.get("group_by_prefix", os.environ.get("VAULTPULL_GROUP_BY_PREFIX", "true")).lower() == "true"
    default_group = s.get("default_group", os.environ.get("VAULTPULL_GROUP_DEFAULT", "default"))

    custom_groups: Dict[str, List[str]] = {}
    if "custom_groups" in s and isinstance(s["custom_groups"], dict):
        custom_groups = {k: _split_csv(v) if isinstance(v, str) else v
                        for k, v in s["custom_groups"].items()}

    return GroupConfig(
        enabled=enabled,
        separator=separator,
        group_by_prefix=group_by_prefix,
        custom_groups=custom_groups,
        default_group=default_group,
    )


def group_secrets(secrets: Dict[str, str], cfg: GroupConfig) -> Dict[str, Dict[str, str]]:
    """Partition secrets into named groups.

    Custom groups take precedence; remaining keys fall back to prefix grouping
    or the default group.
    """
    groups: Dict[str, Dict[str, str]] = {}
    assigned: set = set()

    # Apply custom group assignments first
    for group_name, patterns in cfg.custom_groups.items():
        for key, value in secrets.items():
            if any(key.startswith(p) for p in patterns):
                groups.setdefault(group_name, {})[key] = value
                assigned.add(key)

    # Remaining keys
    for key, value in secrets.items():
        if key in assigned:
            continue
        if cfg.group_by_prefix and cfg.separator in key:
            prefix = key.split(cfg.separator)[0]
            groups.setdefault(prefix, {})[key] = value
        else:
            groups.setdefault(cfg.default_group, {})[key] = value

    return groups
