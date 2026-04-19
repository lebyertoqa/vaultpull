"""Key transformation utilities for normalizing secret keys."""

import re
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class TransformConfig:
    prefix: str = ""
    uppercase: bool = True
    strip_path: bool = True
    key_map: Dict[str, str] = field(default_factory=dict)


def load_transform_config(section: Optional[dict] = None) -> TransformConfig:
    """Load transform config from a config dict section."""
    s = section or {}
    return TransformConfig(
        prefix=s.get("prefix", ""),
        uppercase=str(s.get("uppercase", "true")).lower() != "false",
        strip_path=str(s.get("strip_path", "true")).lower() != "false",
        key_map=s.get("key_map", {}),
    )


def _normalize_key(key: str, strip_path: bool, uppercase: bool) -> str:
    """Normalize a single key: optionally strip path prefix and uppercase."""
    if strip_path and "/" in key:
        key = key.rsplit("/", 1)[-1]
    key = re.sub(r"[^A-Za-z0-9_]", "_", key)
    if uppercase:
        key = key.upper()
    return key


def apply_transform(secrets: Dict[str, str], config: TransformConfig) -> Dict[str, str]:
    """Apply key transformations to a secrets dict.

    Applies in order: strip_path, normalize chars, uppercase, prefix, key_map overrides.
    """
    result: Dict[str, str] = {}
    for raw_key, value in secrets.items():
        new_key = _normalize_key(raw_key, config.strip_path, config.uppercase)
        if config.prefix:
            new_key = config.prefix + new_key
        # key_map can override the final key name
        new_key = config.key_map.get(new_key, new_key)
        result[new_key] = value
    return result
