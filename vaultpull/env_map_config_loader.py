"""Helpers to extract env-map config from a top-level config dict."""
from __future__ import annotations

from typing import Any, Dict, Optional

from vaultpull.secret_env_map import EnvMapConfig, load_env_map_config


def extract_env_map_section(config: Dict[str, Any]) -> Optional[Dict]:
    """Return the [env_map] section dict if present, else None."""
    return config.get("env_map") or config.get("env-map")


def get_env_map_config(config: Dict[str, Any]) -> EnvMapConfig:
    """Load EnvMapConfig from a top-level config dict."""
    section = extract_env_map_section(config)
    return load_env_map_config(section)


def describe_env_map(cfg: EnvMapConfig) -> str:
    """Return a short description of the active env-map configuration."""
    if not cfg.mappings:
        return "env_map: no path->prefix mappings defined"
    parts = ", ".join(f"{p}={px}" for p, px in cfg.mappings.items())
    flags = f"strip_prefix={cfg.strip_prefix}, uppercase={cfg.uppercase}"
    return f"env_map: [{parts}] ({flags})"
