"""Map Vault secret paths to friendly alias names for .env keys."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AliasConfig:
    """Holds path-to-alias mappings and resolution settings."""
    aliases: Dict[str, str] = field(default_factory=dict)  # vault_path -> alias prefix
    strip_prefix: bool = True
    uppercase: bool = True


def _split_pairs(raw: str) -> Dict[str, str]:
    """Parse 'path=alias,path2=alias2' into a dict."""
    result: Dict[str, str] = {}
    for part in raw.split(","):
        part = part.strip()
        if "=" in part:
            k, _, v = part.partition("=")
            result[k.strip()] = v.strip()
    return result


def load_alias_config(cfg_section: Optional[Dict] = None) -> AliasConfig:
    """Load alias config from dict section and/or environment variables."""
    section = cfg_section or {}

    raw_aliases = section.get("aliases") or os.environ.get("VAULTPULL_ALIASES", "")
    aliases = _split_pairs(raw_aliases) if isinstance(raw_aliases, str) else dict(raw_aliases)

    strip_prefix = str(section.get("strip_prefix", os.environ.get("VAULTPULL_ALIAS_STRIP_PREFIX", "true"))).lower() == "true"
    uppercase = str(section.get("uppercase", os.environ.get("VAULTPULL_ALIAS_UPPERCASE", "true"))).lower() == "true"

    return AliasConfig(aliases=aliases, strip_prefix=strip_prefix, uppercase=uppercase)


def resolve_key(vault_path: str, secret_key: str, cfg: AliasConfig) -> str:
    """Produce the final .env key for a given vault path + secret key."""
    prefix = ""
    for path, alias in cfg.aliases.items():
        if vault_path == path or vault_path.startswith(path.rstrip("/") + "/"):
            prefix = alias.rstrip("_") + "_"
            break
    else:
        if not cfg.strip_prefix:
            # Use last segment of path as prefix
            segment = vault_path.strip("/").split("/")[-1]
            prefix = segment.rstrip("_") + "_"

    key = prefix + secret_key
    if cfg.uppercase:
        key = key.upper()
    return key


def apply_aliases(secrets: Dict[str, str], vault_path: str, cfg: AliasConfig) -> Dict[str, str]:
    """Return a new dict with keys renamed according to alias rules."""
    return {resolve_key(vault_path, k, cfg): v for k, v in secrets.items()}
