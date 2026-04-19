"""Secret value validation for vaultpull."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ValidationRule:
    key_pattern: Optional[str] = None   # regex applied to key
    min_length: int = 0
    max_length: int = 65536
    required_keys: List[str] = field(default_factory=list)
    forbidden_keys: List[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    valid: bool
    errors: List[str] = field(default_factory=list)


def load_validation_config(cfg: Optional[dict]) -> ValidationRule:
    """Build a ValidationRule from the [validate] section of config."""
    section = (cfg or {}).get("validate", {})
    return ValidationRule(
        key_pattern=section.get("key_pattern"),
        min_length=int(section.get("min_length", 0)),
        max_length=int(section.get("max_length", 65536)),
        required_keys=[k.strip() for k in section.get("required_keys", "").split(",") if k.strip()],
        forbidden_keys=[k.strip() for k in section.get("forbidden_keys", "").split(",") if k.strip()],
    )


def validate_secrets(secrets: Dict[str, str], rule: ValidationRule) -> ValidationResult:
    """Validate a dict of secrets against a ValidationRule."""
    errors: List[str] = []

    for key in rule.required_keys:
        if key not in secrets:
            errors.append(f"Required key missing: {key}")

    for key in rule.forbidden_keys:
        if key in secrets:
            errors.append(f"Forbidden key present: {key}")

    pattern = re.compile(rule.key_pattern) if rule.key_pattern else None

    for key, value in secrets.items():
        if pattern and not pattern.match(key):
            errors.append(f"Key '{key}' does not match pattern '{rule.key_pattern}'")
        if len(value) < rule.min_length:
            errors.append(f"Key '{key}' value too short (min {rule.min_length})")
        if len(value) > rule.max_length:
            errors.append(f"Key '{key}' value too long (max {rule.max_length})")

    return ValidationResult(valid=len(errors) == 0, errors=errors)
