"""Helper to extract and describe lint config from a top-level config dict."""
from __future__ import annotations

from typing import Dict

from vaultpull.lint_config import LintConfig, load_lint_config


def extract_lint_section(cfg: Dict) -> Dict:
    """Return the raw [lint] section or empty dict."""
    return cfg.get("lint", {})


def get_lint_config(cfg: Dict | None = None) -> LintConfig:
    """Convenience wrapper — load LintConfig from full config dict."""
    return load_lint_config(cfg)


def describe_lint(cfg: LintConfig) -> str:
    """Return a human-readable summary of the active lint configuration."""
    if not cfg.enabled:
        return "Linting: disabled"
    parts = ["Linting: enabled"]
    if cfg.fail_on_error:
        parts.append("fail-on-error")
    if cfg.skip_keys:
        parts.append(f"skip-keys={','.join(cfg.skip_keys)}")
    if cfg.skip_convention_check:
        parts.append("skip-convention")
    if cfg.skip_weak_check:
        parts.append("skip-weak")
    return " | ".join(parts)
