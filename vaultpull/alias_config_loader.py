"""Extract alias configuration from the top-level config dict."""
from __future__ import annotations

from typing import Any, Dict, Optional

from vaultpull.path_alias import AliasConfig, load_alias_config

_SECTION_KEY = "alias"


def extract_alias_section(config: Dict[str, Any]) -> Optional[Dict]:
    """Return the [alias] section dict if present, else None."""
    return config.get(_SECTION_KEY)


def get_alias_config(config: Dict[str, Any]) -> AliasConfig:
    """Load AliasConfig from a full vaultpull config dict."""
    section = extract_alias_section(config)
    return load_alias_config(section)


def describe_aliases(cfg: AliasConfig) -> str:
    """Return a short human-readable description of the alias config."""
    if not cfg.aliases:
        return "No path aliases configured."
    parts = [f"{path} -> {alias}" for path, alias in cfg.aliases.items()]
    flags = f"strip_prefix={cfg.strip_prefix}, uppercase={cfg.uppercase}"
    return "Aliases: " + "; ".join(parts) + f" ({flags})"
