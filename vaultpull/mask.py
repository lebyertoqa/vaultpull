"""Masking utilities for sensitive secret values in logs and output."""

from typing import Dict

DEFAULT_MASK = "****"
SENSITIVE_PATTERNS = (
    "password", "secret", "token", "key", "api", "auth", "credential", "private",
)


def is_sensitive(key: str) -> bool:
    """Return True if the key name suggests a sensitive value."""
    lower = key.lower()
    return any(pat in lower for pat in SENSITIVE_PATTERNS)


def mask_value(value: str, visible_chars: int = 0) -> str:
    """Return a masked version of value, optionally showing trailing chars."""
    if not value:
        return DEFAULT_MASK
    if visible_chars > 0 and len(value) > visible_chars:
        return DEFAULT_MASK + value[-visible_chars:]
    return DEFAULT_MASK


def mask_secrets(
    secrets: Dict[str, str],
    visible_chars: int = 0,
    force_mask_all: bool = False,
) -> Dict[str, str]:
    """Return a copy of secrets dict with sensitive values masked.

    Args:
        secrets: Original key/value pairs.
        visible_chars: Number of trailing characters to reveal.
        force_mask_all: If True, mask every key regardless of name.
    """
    result: Dict[str, str] = {}
    for key, value in secrets.items():
        if force_mask_all or is_sensitive(key):
            result[key] = mask_value(value, visible_chars)
        else:
            result[key] = value
    return result
