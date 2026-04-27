"""Secret priority scoring — rank secrets by importance for display and processing order."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

# Keywords that indicate high-priority secrets
_HIGH_KEYWORDS = ("password", "secret", "token", "key", "cert", "private", "credential")
_MEDIUM_KEYWORDS = ("api", "auth", "access", "db", "database", "host", "url", "endpoint")


def _split_csv(value: str) -> List[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass
class PriorityConfig:
    high_keywords: List[str] = field(default_factory=lambda: list(_HIGH_KEYWORDS))
    medium_keywords: List[str] = field(default_factory=lambda: list(_MEDIUM_KEYWORDS))
    pinned_keys: List[str] = field(default_factory=list)


def load_priority_config(section: dict | None = None) -> PriorityConfig:
    """Build PriorityConfig from an optional config dict."""
    sec = section or {}
    return PriorityConfig(
        high_keywords=_split_csv(sec.get("high_keywords", ",".join(_HIGH_KEYWORDS))),
        medium_keywords=_split_csv(sec.get("medium_keywords", ",".join(_MEDIUM_KEYWORDS))),
        pinned_keys=_split_csv(sec.get("pinned_keys", "")),
    )


def score_secret(key: str, cfg: PriorityConfig) -> int:
    """Return a numeric priority score for *key* (higher = more important)."""
    lower = key.lower()
    if key in cfg.pinned_keys:
        return 100
    for kw in cfg.high_keywords:
        if kw in lower:
            return 80
    for kw in cfg.medium_keywords:
        if kw in lower:
            return 50
    return 10


@dataclass
class PriorityReport:
    environment: str
    scores: Dict[str, int]
    ordered: List[Tuple[str, int]]


def build_priority_report(
    secrets: Dict[str, str],
    cfg: PriorityConfig,
    environment: str = "default",
) -> PriorityReport:
    scores = {k: score_secret(k, cfg) for k in secrets}
    ordered = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return PriorityReport(environment=environment, scores=scores, ordered=ordered)


def format_priority_report(report: PriorityReport) -> str:
    lines = [f"Priority report [{report.environment}]  ({len(report.scores)} keys)"]
    for key, score in report.ordered:
        label = "HIGH" if score >= 80 else ("MED" if score >= 50 else "LOW")
        lines.append(f"  [{label:4s}] {key}")
    return "\n".join(lines)
