"""Secret scope management: restrict which Vault paths are accessible per environment."""

from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ScopeConfig:
    environment: str
    allowed_paths: List[str] = field(default_factory=list)
    denied_paths: List[str] = field(default_factory=list)
    strict: bool = False  # if True, deny anything not explicitly allowed


def _split_csv(value: str) -> List[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def load_scope_config(cfg: Optional[Dict] = None) -> ScopeConfig:
    """Load ScopeConfig from optional config dict section, falling back to env vars."""
    section = cfg or {}

    environment = (
        section.get("environment")
        or os.environ.get("VAULTPULL_ENVIRONMENT", "default")
    )

    allowed_raw = section.get("allowed_paths") or os.environ.get("VAULTPULL_ALLOWED_PATHS", "")
    denied_raw = section.get("denied_paths") or os.environ.get("VAULTPULL_DENIED_PATHS", "")

    strict_raw = section.get("strict") or os.environ.get("VAULTPULL_SCOPE_STRICT", "false")
    strict = str(strict_raw).lower() in ("1", "true", "yes")

    return ScopeConfig(
        environment=environment,
        allowed_paths=_split_csv(allowed_raw) if isinstance(allowed_raw, str) else list(allowed_raw),
        denied_paths=_split_csv(denied_raw) if isinstance(denied_raw, str) else list(denied_raw),
        strict=strict,
    )


def is_path_allowed(path: str, scope: ScopeConfig) -> bool:
    """Return True if the given Vault path is permitted under the scope rules."""
    # Deny list takes priority
    for pattern in scope.denied_paths:
        if fnmatch.fnmatch(path, pattern):
            return False

    if scope.strict:
        # Must match at least one allowed pattern
        if not scope.allowed_paths:
            return False
        return any(fnmatch.fnmatch(path, p) for p in scope.allowed_paths)

    # Non-strict: allowed if no allow-list, or matches allow-list
    if scope.allowed_paths:
        return any(fnmatch.fnmatch(path, p) for p in scope.allowed_paths)

    return True


def filter_paths(paths: List[str], scope: ScopeConfig) -> List[str]:
    """Return only the paths permitted by the scope configuration."""
    return [p for p in paths if is_path_allowed(p, scope)]
