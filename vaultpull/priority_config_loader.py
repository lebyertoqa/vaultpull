"""Helpers to extract priority config from a broader vaultpull config dict."""
from __future__ import annotations

from typing import Dict

from vaultpull.secret_priority import PriorityConfig, load_priority_config

_SECTION = "priority"


def extract_priority_section(config: Dict) -> Dict:
    """Return the [priority] sub-dict from a full config, or {}."""
    return config.get(_SECTION, {})


def get_priority_config(config: Dict) -> PriorityConfig:
    """Convenience: load PriorityConfig from a full config dict."""
    return load_priority_config(extract_priority_section(config))


def describe_priority(cfg: PriorityConfig) -> str:
    pinned = ", ".join(cfg.pinned_keys) if cfg.pinned_keys else "(none)"
    return (
        f"PriorityConfig "
        f"high_keywords={cfg.high_keywords} "
        f"medium_keywords={cfg.medium_keywords} "
        f"pinned={pinned}"
    )
