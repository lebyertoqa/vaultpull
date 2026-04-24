"""Maps Vault secret paths to environment variable name prefixes."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


def _split_pairs(raw: str) -> Dict[str, str]:
    """Parse 'path=PREFIX,path2=PREFIX2' into a dict."""
    result: Dict[str, str] = {}
    for part in raw.split(","):
        part = part.strip()
        if "=" in part:
            k, _, v = part.partition("=")
            result[k.strip()] = v.strip()
    return result


@dataclass
class EnvMapConfig:
    mappings: Dict[str, str] = field(default_factory=dict)  # path -> ENV_PREFIX
    strip_prefix: bool = True
    uppercase: bool = True


def load_env_map_config(section: Optional[Dict] = None) -> EnvMapConfig:
    """Load env-map config from dict section and/or environment variables."""
    section = section or {}

    raw_mappings = section.get(
        "mappings", os.environ.get("VAULTPULL_ENV_MAPPINGS", "")
    )
    mappings = _split_pairs(raw_mappings) if raw_mappings else {}

    strip_prefix = str(
        section.get("strip_prefix", os.environ.get("VAULTPULL_ENV_STRIP_PREFIX", "true"))
    ).lower() == "true"

    uppercase = str(
        section.get("uppercase", os.environ.get("VAULTPULL_ENV_UPPERCASE", "true"))
    ).lower() == "true"

    return EnvMapConfig(mappings=mappings, strip_prefix=strip_prefix, uppercase=uppercase)


def apply_env_prefix(key: str, path: str, cfg: EnvMapConfig) -> str:
    """Apply prefix mapping to a secret key based on its Vault path."""
    prefix = cfg.mappings.get(path, "")

    if cfg.strip_prefix and "/" in key:
        key = key.rsplit("/", 1)[-1]

    if cfg.uppercase:
        key = key.upper()

    if prefix:
        sep = "_" if not prefix.endswith("_") else ""
        key = f"{prefix}{sep}{key}"

    return key


def map_secrets(
    secrets: Dict[str, str], path: str, cfg: EnvMapConfig
) -> Dict[str, str]:
    """Return a new dict with keys renamed according to env-map config."""
    return {apply_env_prefix(k, path, cfg): v for k, v in secrets.items()}
