"""Integrate ScopeConfig loading into the main vaultpull config pipeline."""

from __future__ import annotations

from typing import Any, Dict, Optional

from vaultpull.secret_scope import ScopeConfig, load_scope_config

_SECTION_KEY = "scope"


def extract_scope_section(raw_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Pull the [scope] section from the top-level config dict, if present."""
    return raw_config.get(_SECTION_KEY)


def get_scope_config(raw_config: Optional[Dict[str, Any]] = None) -> ScopeConfig:
    """
    Convenience wrapper: extract the scope section from a raw config dict
    and return a fully resolved ScopeConfig.

    Falls back to environment variables when keys are absent.
    """
    section = extract_scope_section(raw_config or {})
    return load_scope_config(section)


def describe_scope(scope: ScopeConfig) -> str:
    """Return a one-line description of the active scope for logging."""
    parts = [f"env={scope.environment}"]
    if scope.allowed_paths:
        parts.append(f"allowed={len(scope.allowed_paths)} pattern(s)")
    if scope.denied_paths:
        parts.append(f"denied={len(scope.denied_paths)} pattern(s)")
    if scope.strict:
        parts.append("strict=true")
    return "ScopeConfig[" + ", ".join(parts) + "]"
