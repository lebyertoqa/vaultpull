"""Key filtering support: include/exclude secrets by prefix or pattern."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FilterConfig:
    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    prefix_strip: Optional[str] = None


def load_filter_config(cfg: Optional[dict] = None) -> FilterConfig:
    """Build FilterConfig from an optional config dict section."""
    section = cfg or {}
    raw_include = section.get("include_patterns", "")
    raw_exclude = section.get("exclude_patterns", "")

    def _split(val: object) -> List[str]:
        if isinstance(val, list):
            return [str(v).strip() for v in val if str(v).strip()]
        return [p.strip() for p in str(val).split(",") if p.strip()]

    return FilterConfig(
        include_patterns=_split(raw_include),
        exclude_patterns=_split(raw_exclude),
        prefix_strip=section.get("prefix_strip") or None,
    )


def _matches(key: str, patterns: List[str]) -> bool:
    return any(fnmatch.fnmatch(key, p) for p in patterns)


def apply_filter(secrets: Dict[str, str], config: FilterConfig) -> Dict[str, str]:
    """Return a filtered (and optionally prefix-stripped) copy of secrets."""
    result: Dict[str, str] = {}

    for key, value in secrets.items():
        # Include filter: if patterns defined, key must match at least one
        if config.include_patterns and not _matches(key, config.include_patterns):
            continue
        # Exclude filter: skip if matches any exclude pattern
        if config.exclude_patterns and _matches(key, config.exclude_patterns):
            continue

        out_key = key
        if config.prefix_strip and key.startswith(config.prefix_strip):
            out_key = key[len(config.prefix_strip):]

        if out_key:
            result[out_key] = value

    return result
