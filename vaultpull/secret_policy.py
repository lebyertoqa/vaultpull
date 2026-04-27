"""Secret policy enforcement: check secrets against allowed/denied key patterns and value constraints."""
from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


def _split_csv(value: str) -> List[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass
class PolicyConfig:
    allowed_keys: List[str] = field(default_factory=list)   # glob patterns
    denied_keys: List[str] = field(default_factory=list)    # glob patterns
    max_value_length: int = 0                               # 0 = unlimited
    require_non_empty: bool = True
    environment: str = "default"


def load_policy_config(section: Optional[Dict] = None) -> PolicyConfig:
    """Load PolicyConfig from an optional config dict, falling back to env vars."""
    section = section or {}

    allowed_raw = section.get("allowed_keys") or os.environ.get("VAULTPULL_POLICY_ALLOWED_KEYS", "")
    denied_raw = section.get("denied_keys") or os.environ.get("VAULTPULL_POLICY_DENIED_KEYS", "")

    max_len_raw = section.get("max_value_length") or os.environ.get("VAULTPULL_POLICY_MAX_VALUE_LENGTH", "0")
    try:
        max_value_length = int(max_len_raw)
    except (TypeError, ValueError):
        max_value_length = 0

    require_raw = section.get("require_non_empty") or os.environ.get("VAULTPULL_POLICY_REQUIRE_NON_EMPTY", "true")
    require_non_empty = str(require_raw).lower() not in ("false", "0", "no")

    environment = section.get("environment") or os.environ.get("VAULTPULL_ENVIRONMENT", "default")

    return PolicyConfig(
        allowed_keys=_split_csv(allowed_raw) if allowed_raw else [],
        denied_keys=_split_csv(denied_raw) if denied_raw else [],
        max_value_length=max_value_length,
        require_non_empty=require_non_empty,
        environment=environment,
    )


@dataclass
class PolicyViolation:
    key: str
    reason: str


@dataclass
class PolicyReport:
    environment: str
    violations: List[PolicyViolation] = field(default_factory=list)
    checked: int = 0

    @property
    def has_violations(self) -> bool:
        return len(self.violations) > 0


def _key_allowed(key: str, cfg: PolicyConfig) -> bool:
    if cfg.allowed_keys and not any(fnmatch.fnmatch(key, p) for p in cfg.allowed_keys):
        return False
    return True


def _key_denied(key: str, cfg: PolicyConfig) -> bool:
    return any(fnmatch.fnmatch(key, p) for p in cfg.denied_keys)


def enforce_policy(secrets: Dict[str, str], cfg: PolicyConfig) -> PolicyReport:
    """Evaluate secrets against the policy and return a PolicyReport."""
    report = PolicyReport(environment=cfg.environment)
    for key, value in secrets.items():
        report.checked += 1
        if not _key_allowed(key, cfg):
            report.violations.append(PolicyViolation(key=key, reason="key not in allowed_keys patterns"))
            continue
        if _key_denied(key, cfg):
            report.violations.append(PolicyViolation(key=key, reason="key matches denied_keys pattern"))
            continue
        if cfg.require_non_empty and not value:
            report.violations.append(PolicyViolation(key=key, reason="value is empty"))
        if cfg.max_value_length and len(value) > cfg.max_value_length:
            report.violations.append(
                PolicyViolation(key=key, reason=f"value exceeds max length {cfg.max_value_length}")
            )
    return report
