"""Integration helper: run validation inside the sync pipeline."""
from __future__ import annotations

from typing import Dict, Optional

from vaultpull.validate import ValidationResult, ValidationRule, load_validation_config, validate_secrets


def run_validation(
    secrets: Dict[str, str],
    raw_config: Optional[dict],
    *,
    strict: bool = False,
) -> ValidationResult:
    """Load validation rules from config and validate *secrets*.

    Args:
        secrets:    The fetched secret key/value pairs.
        raw_config: The full parsed config dict (may contain a [validate] section).
        strict:     If True, raise ValueError on validation failure instead of
                    returning the result — useful for CI / pre-commit hooks.

    Returns:
        ValidationResult with .valid and .errors populated.
    """
    rule: ValidationRule = load_validation_config(raw_config)
    result: ValidationResult = validate_secrets(secrets, rule)

    if not result.valid and strict:
        formatted = "\n".join(f"  - {e}" for e in result.errors)
        raise ValueError(f"Secret validation failed:\n{formatted}")

    return result


def format_validation_report(result: ValidationResult) -> str:
    """Return a human-readable validation report string."""
    if result.valid:
        return "Validation passed — all secrets are valid."
    lines = [f"Validation failed with {len(result.errors)} error(s):"]
    for err in result.errors:
        lines.append(f"  • {err}")
    return "\n".join(lines)
