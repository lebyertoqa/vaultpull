"""Secret namespace isolation — partition secrets by logical namespace."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


def _split_csv(value: str) -> List[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass
class NamespaceConfig:
    enabled: bool = False
    default_namespace: str = "default"
    allowed_namespaces: List[str] = field(default_factory=list)
    separator: str = "/"
    strip_namespace: bool = True


def load_namespace_config(section: Optional[Dict] = None) -> NamespaceConfig:
    """Load namespace config from a config dict section with env fallbacks."""
    import os

    s = section or {}

    enabled = str(s.get("enabled", os.getenv("VAULTPULL_NS_ENABLED", "false"))).lower() == "true"
    default_namespace = s.get("default_namespace", os.getenv("VAULTPULL_NS_DEFAULT", "default"))
    separator = s.get("separator", os.getenv("VAULTPULL_NS_SEPARATOR", "/"))
    strip_namespace = str(
        s.get("strip_namespace", os.getenv("VAULTPULL_NS_STRIP", "true"))
    ).lower() == "true"

    raw_allowed = s.get("allowed_namespaces", os.getenv("VAULTPULL_NS_ALLOWED", ""))
    if isinstance(raw_allowed, list):
        allowed_namespaces = [str(v).strip() for v in raw_allowed if str(v).strip()]
    else:
        allowed_namespaces = _split_csv(str(raw_allowed))

    return NamespaceConfig(
        enabled=enabled,
        default_namespace=default_namespace,
        allowed_namespaces=allowed_namespaces,
        separator=separator,
        strip_namespace=strip_namespace,
    )


def extract_namespace(key: str, cfg: NamespaceConfig) -> tuple[str, str]:
    """Return (namespace, bare_key) for a given secret key."""
    sep = cfg.separator
    if sep in key:
        ns, _, bare = key.partition(sep)
        return ns, bare
    return cfg.default_namespace, key


def is_namespace_allowed(namespace: str, cfg: NamespaceConfig) -> bool:
    """Return True if the namespace is permitted under the current config."""
    if not cfg.allowed_namespaces:
        return True
    return namespace in cfg.allowed_namespaces


def partition_secrets(
    secrets: Dict[str, str], cfg: NamespaceConfig
) -> Dict[str, Dict[str, str]]:
    """Group secrets by namespace, optionally stripping the namespace prefix."""
    result: Dict[str, Dict[str, str]] = {}
    for key, value in secrets.items():
        ns, bare = extract_namespace(key, cfg)
        if not is_namespace_allowed(ns, cfg):
            continue
        out_key = bare if cfg.strip_namespace else key
        result.setdefault(ns, {})[out_key] = value
    return result
