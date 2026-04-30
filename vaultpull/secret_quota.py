"""Secret quota enforcement — limits the number of secrets synced per run."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


@dataclass
class QuotaConfig:
    max_secrets: int = 0          # 0 = unlimited
    max_per_path: int = 0         # 0 = unlimited
    warn_threshold: int = 0       # 0 = no warning
    strict: bool = False          # True = hard-fail on breach


def load_quota_config(section: Optional[Dict] = None) -> QuotaConfig:
    """Load quota config from an optional dict section, falling back to env vars."""
    s = section or {}
    return QuotaConfig(
        max_secrets=int(s.get("max_secrets", _int_env("VAULTPULL_QUOTA_MAX_SECRETS", 0))),
        max_per_path=int(s.get("max_per_path", _int_env("VAULTPULL_QUOTA_MAX_PER_PATH", 0))),
        warn_threshold=int(s.get("warn_threshold", _int_env("VAULTPULL_QUOTA_WARN_THRESHOLD", 0))),
        strict=str(s.get("strict", os.environ.get("VAULTPULL_QUOTA_STRICT", "false"))).lower() == "true",
    )


@dataclass
class QuotaViolation:
    kind: str          # "global" | "per_path"
    path: str
    count: int
    limit: int

    @property
    def message(self) -> str:
        return f"Quota breach [{self.kind}] path={self.path!r}: {self.count} secrets exceeds limit of {self.limit}"


@dataclass
class QuotaReport:
    total: int
    per_path: Dict[str, int]
    violations: List[QuotaViolation] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return bool(self.violations)


def check_quota(secrets: Dict[str, str], cfg: QuotaConfig, path: str = "<root>") -> QuotaReport:
    """Evaluate quota constraints against a flat secrets dict."""
    from collections import defaultdict

    per_path: Dict[str, int] = defaultdict(int)
    for key in secrets:
        prefix = key.split("/")[0] if "/" in key else path
        per_path[prefix] += 1

    total = len(secrets)
    violations: List[QuotaViolation] = []
    warnings: List[str] = []

    if cfg.max_secrets and total > cfg.max_secrets:
        violations.append(QuotaViolation("global", path, total, cfg.max_secrets))

    if cfg.max_per_path:
        for p, count in per_path.items():
            if count > cfg.max_per_path:
                violations.append(QuotaViolation("per_path", p, count, cfg.max_per_path))

    if cfg.warn_threshold and total >= cfg.warn_threshold and not violations:
        warnings.append(f"Secret count {total} is at or above warn threshold {cfg.warn_threshold}")

    return QuotaReport(total=total, per_path=dict(per_path), violations=violations, warnings=warnings)
