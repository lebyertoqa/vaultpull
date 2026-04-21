"""Load merge configuration from a config dict or environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from vaultpull.env_merge import MergeStrategy, load_merge_strategy

_SECTION = "merge"


@dataclass
class MergeConfig:
    strategy: MergeStrategy = MergeStrategy.OVERWRITE
    # Keys that should never be overwritten regardless of strategy
    protected_keys: List[str] = field(default_factory=list)
    # If True, keys present locally but absent in Vault are removed
    remove_stale: bool = False


def _split_csv(value: str) -> List[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name, "").lower()
    if raw in ("1", "true", "yes"):
        return True
    if raw in ("0", "false", "no"):
        return False
    return default


def load_merge_config(cfg: Optional[Dict[str, Any]] = None) -> MergeConfig:
    """Build a :class:`MergeConfig` from an optional config dict section.

    Priority (highest → lowest):
    1. Values present in *cfg* (the ``[merge]`` section of vaultpull.toml)
    2. Environment variables (``VAULTPULL_MERGE_*``)
    3. Hard-coded defaults
    """
    section: Dict[str, Any] = {}
    if cfg and _SECTION in cfg:
        section = cfg[_SECTION]

    # strategy
    raw_strategy = section.get(
        "strategy", os.environ.get("VAULTPULL_MERGE_STRATEGY")
    )
    strategy = load_merge_strategy(raw_strategy)

    # protected_keys
    raw_protected = section.get("protected_keys")
    if raw_protected is None:
        env_val = os.environ.get("VAULTPULL_MERGE_PROTECTED_KEYS", "")
        protected_keys = _split_csv(env_val) if env_val else []
    elif isinstance(raw_protected, list):
        protected_keys = raw_protected
    else:
        protected_keys = _split_csv(str(raw_protected))

    # remove_stale
    if "remove_stale" in section:
        remove_stale = bool(section["remove_stale"])
    else:
        remove_stale = _bool_env("VAULTPULL_MERGE_REMOVE_STALE", default=False)

    return MergeConfig(
        strategy=strategy,
        protected_keys=protected_keys,
        remove_stale=remove_stale,
    )
