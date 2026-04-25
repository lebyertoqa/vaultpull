"""Lint secrets for common issues: empty values, weak patterns, naming conventions."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


_WEAK_PATTERNS = [
    re.compile(r"^(password|secret|changeme|test|example|placeholder)$", re.I),
    re.compile(r"^(.{1,4})$"),  # very short values
]

_KEY_CONVENTION = re.compile(r"^[A-Z][A-Z0-9_]*$")


@dataclass
class LintIssue:
    key: str
    severity: str  # "error" | "warning" | "info"
    message: str


@dataclass
class LintReport:
    environment: str
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)


def _check_key_convention(key: str) -> Optional[LintIssue]:
    if not _KEY_CONVENTION.match(key):
        return LintIssue(key=key, severity="warning",
                         message=f"Key '{key}' does not follow UPPER_SNAKE_CASE convention")
    return None


def _check_empty_value(key: str, value: str) -> Optional[LintIssue]:
    if value.strip() == "":
        return LintIssue(key=key, severity="error",
                         message=f"Key '{key}' has an empty value")
    return None


def _check_weak_value(key: str, value: str) -> Optional[LintIssue]:
    for pattern in _WEAK_PATTERNS:
        if pattern.match(value):
            return LintIssue(key=key, severity="warning",
                             message=f"Key '{key}' appears to have a weak or placeholder value")
    return None


def lint_secrets(secrets: Dict[str, str], environment: str = "default") -> LintReport:
    report = LintReport(environment=environment)
    for key, value in secrets.items():
        for checker in (_check_key_convention, _check_empty_value, _check_weak_value):
            issue = checker(key, value)
            if issue:
                report.issues.append(issue)
    return report


def format_lint_report(report: LintReport) -> str:
    lines = [f"Lint report [{report.environment}]"]
    if not report.issues:
        lines.append("  No issues found.")
        return "\n".join(lines)
    for issue in report.issues:
        prefix = {"error": "[ERROR]", "warning": "[WARN] ", "info": "[INFO] "}.get(issue.severity, "[?]")
        lines.append(f"  {prefix} {issue.message}")
    lines.append(f"  Total: {len(report.errors)} error(s), {len(report.warnings)} warning(s)")
    return "\n".join(lines)
