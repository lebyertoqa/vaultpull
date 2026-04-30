"""Helpers to extract quota config from a parsed vaultpull config dict."""
from __future__ import annotations

from typing import Dict, Optional

from vaultpull.secret_quota import QuotaConfig, load_quota_config


def extract_quota_section(config: Dict) -> Optional[Dict]:
    """Return the [quota] section from a parsed config dict, or None."""
    return config.get("quota") or config.get("QUOTA") or None


def get_quota_config(config: Dict) -> QuotaConfig:
    """Convenience: extract section and build QuotaConfig in one call."""
    return load_quota_config(extract_quota_section(config))


def describe_quota(cfg: QuotaConfig) -> str:
    """Return a human-readable summary of the active quota settings."""
    parts = []
    if cfg.max_secrets:
        parts.append(f"max_secrets={cfg.max_secrets}")
    if cfg.max_per_path:
        parts.append(f"max_per_path={cfg.max_per_path}")
    if cfg.warn_threshold:
        parts.append(f"warn_threshold={cfg.warn_threshold}")
    if cfg.strict:
        parts.append("strict=true")
    return "quota(" + ", ".join(parts) + ")" if parts else "quota(unlimited)"
