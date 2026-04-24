"""Helper to extract expiry section from a top-level config dict."""
from __future__ import annotations

from typing import Any, Dict, Optional

from vaultpull.secret_expiry import ExpiryConfig, load_expiry_config


def extract_expiry_section(config: Dict[str, Any]) -> Optional[Dict]:
    """Return the [expiry] sub-dict from a parsed config, or None."""
    return config.get("expiry") if isinstance(config, dict) else None


def get_expiry_config(config: Dict[str, Any]) -> ExpiryConfig:
    """Convenience: load ExpiryConfig from a full config mapping."""
    return load_expiry_config(extract_expiry_section(config))


def describe_expiry(cfg: ExpiryConfig) -> str:
    """Return a human-readable summary of the expiry configuration."""
    parts = [
        f"enabled={cfg.enabled}",
        f"warn_before_days={cfg.warn_before_days}",
        f"fail_on_expired={cfg.fail_on_expired}",
    ]
    return "ExpiryConfig(" + ", ".join(parts) + ")"
