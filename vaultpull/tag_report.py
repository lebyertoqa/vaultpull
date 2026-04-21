"""Build and format a report summarising tag-based filtering."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from vaultpull.secret_tags import TagConfig, apply_tag_filter


@dataclass
class TagReport:
    environment: str
    total_input: int
    total_passed: int
    total_excluded: int
    required_tags: List[str] = field(default_factory=list)
    excluded_tags: List[str] = field(default_factory=list)
    strict: bool = False


def build_tag_report(
    secrets: Dict[str, Dict],
    cfg: TagConfig,
    environment: str = "default",
) -> TagReport:
    """Run tag filtering and return a TagReport describing the outcome."""
    passed = apply_tag_filter(secrets, cfg)
    return TagReport(
        environment=environment,
        total_input=len(secrets),
        total_passed=len(passed),
        total_excluded=len(secrets) - len(passed),
        required_tags=list(cfg.required_tags),
        excluded_tags=list(cfg.excluded_tags),
        strict=cfg.strict,
    )


def format_tag_report(report: TagReport) -> str:
    """Return a human-readable summary of the tag filter report."""
    lines = [
        f"Tag Filter Report [{report.environment}]",
        f"  Input secrets : {report.total_input}",
        f"  Passed        : {report.total_passed}",
        f"  Excluded      : {report.total_excluded}",
        f"  Strict mode   : {'yes' if report.strict else 'no'}",
    ]
    if report.required_tags:
        lines.append(f"  Required tags : {', '.join(report.required_tags)}")
    if report.excluded_tags:
        lines.append(f"  Excluded tags : {', '.join(report.excluded_tags)}")
    return "\n".join(lines)
