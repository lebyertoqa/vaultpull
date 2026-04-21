"""Helpers to extract tag config from a vaultpull config dict."""
from __future__ import annotations

from typing import Any, Dict

from vaultpull.secret_tags import TagConfig, load_tag_config


def extract_tag_section(config: Dict[str, Any]) -> Dict:
    """Pull the [tags] section from a full config dict, or return empty dict."""
    return config.get("tags", {})


def get_tag_config(config: Dict[str, Any]) -> TagConfig:
    """Convenience wrapper: parse TagConfig from a full config dict."""
    return load_tag_config(extract_tag_section(config))


def describe_tags(cfg: TagConfig) -> str:
    """Return a one-line human description of the active tag config."""
    parts = []
    if cfg.required_tags:
        parts.append(f"require={','.join(cfg.required_tags)}")
    if cfg.excluded_tags:
        parts.append(f"exclude={','.join(cfg.excluded_tags)}")
    if cfg.strict:
        parts.append("strict=true")
    if not parts:
        return "tag filtering: disabled"
    return "tag filtering: " + " | ".join(parts)
