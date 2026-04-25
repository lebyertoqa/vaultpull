"""Load lint configuration from config dict or environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List


def _split_csv(value: str) -> List[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def _bool_env(name: str, default: bool = False) -> bool:
    val = os.environ.get(name, "").lower()
    if val in ("1", "true", "yes"):
        return True
    if val in ("0", "false", "no"):
        return False
    return default


@dataclass
class LintConfig:
    enabled: bool = True
    fail_on_error: bool = False
    skip_keys: List[str] = field(default_factory=list)
    skip_convention_check: bool = False
    skip_weak_check: bool = False


def load_lint_config(cfg: Dict | None = None) -> LintConfig:
    section: Dict = (cfg or {}).get("lint", {})

    def _get(key: str, env_var: str, default: str) -> str:
        return section.get(key) or os.environ.get(env_var, default)

    enabled_raw = _get("enabled", "VAULTPULL_LINT_ENABLED", "true").lower()
    enabled = enabled_raw in ("1", "true", "yes")

    fail_raw = _get("fail_on_error", "VAULTPULL_LINT_FAIL_ON_ERROR", "false").lower()
    fail_on_error = fail_raw in ("1", "true", "yes")

    skip_keys_raw = section.get("skip_keys") or os.environ.get("VAULTPULL_LINT_SKIP_KEYS", "")
    skip_keys = _split_csv(skip_keys_raw) if skip_keys_raw else []

    skip_convention = _bool_env("VAULTPULL_LINT_SKIP_CONVENTION",
                                 section.get("skip_convention_check", False))
    skip_weak = _bool_env("VAULTPULL_LINT_SKIP_WEAK",
                           section.get("skip_weak_check", False))

    return LintConfig(
        enabled=enabled,
        fail_on_error=fail_on_error,
        skip_keys=skip_keys,
        skip_convention_check=skip_convention,
        skip_weak_check=skip_weak,
    )
