"""Redact secrets from log output and error messages before they are written."""

import re
from typing import Dict, Optional

# Patterns that suggest a value should be fully redacted in output
_REDACT_PATTERNS = [
    re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key|private[_-]?key|auth)"),
]

_PLACEHOLDER = "[REDACTED]"
_PARTIAL_VISIBLE = 4  # characters visible at the start when partially shown


def should_redact(key: str) -> bool:
    """Return True if the key name suggests the value must be fully redacted."""
    for pattern in _REDACT_PATTERNS:
        if pattern.search(key):
            return True
    return False


def redact_value(key: str, value: str, partial: bool = False) -> str:
    """Return a redacted representation of *value* based on *key* sensitivity.

    Args:
        key: The secret key name used to determine sensitivity.
        value: The plaintext secret value.
        partial: When True and the value is long enough, show the first few
                 characters followed by asterisks instead of the full placeholder.
    """
    if not should_redact(key):
        return value

    if partial and len(value) > _PARTIAL_VISIBLE + 2:
        visible = value[:_PARTIAL_VISIBLE]
        return f"{visible}{'*' * 6}"

    return _PLACEHOLDER


def redact_dict(
    secrets: Dict[str, str],
    partial: bool = False,
    safe_keys: Optional[set] = None,
) -> Dict[str, str]:
    """Return a copy of *secrets* with sensitive values redacted.

    Args:
        secrets: Mapping of key -> plaintext value.
        partial: Passed through to :func:`redact_value`.
        safe_keys: Optional set of keys that are explicitly safe and must not
                   be redacted regardless of their name.
    """
    safe_keys = safe_keys or set()
    return {
        k: (v if k in safe_keys else redact_value(k, v, partial=partial))
        for k, v in secrets.items()
    }


def redact_message(message: str, secrets: Dict[str, str]) -> str:
    """Replace any plaintext secret values found in *message* with the redacted placeholder.

    Only secrets whose keys are considered sensitive are replaced.
    """
    for key, value in secrets.items():
        if should_redact(key) and value and value in message:
            message = message.replace(value, _PLACEHOLDER)
    return message
