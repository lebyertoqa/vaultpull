"""Helpers to extract group config from a parsed config dict."""
from __future__ import annotations

from typing import Any, Dict, Optional

from vaultpull.secret_group import GroupConfig, load_group_config

_SECTION = "group"


def extract_group_section(config: Dict[str, Any]) -> Optional[Dict]:
    """Return the [group] section dict if present, else None."""
    return config.get(_SECTION)


def get_group_config(config: Dict[str, Any]) -> GroupConfig:
    """Load GroupConfig from a top-level config dict."""
    return load_group_config(extract_group_section(config))


def describe_group(cfg: GroupConfig) -> str:
    """Return a one-line human description of the active group config."""
    if not cfg.enabled:
        return "grouping disabled"
    parts = [f"separator='{cfg.separator}'"]
    if cfg.group_by_prefix:
        parts.append("group_by_prefix=true")
    if cfg.custom_groups:
        names = ", ".join(sorted(cfg.custom_groups))
        parts.append(f"custom_groups=[{names}]")
    return "grouping enabled: " + ", ".join(parts)
