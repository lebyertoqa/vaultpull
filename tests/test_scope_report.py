"""Tests for vaultpull.scope_report."""

import pytest

from vaultpull.secret_scope import ScopeConfig
from vaultpull.scope_report import ScopeReport, build_scope_report, format_scope_report


PATHS = [
    "secret/app/db",
    "secret/app/cache",
    "secret/legacy/old",
    "secret/infra/tls",
]


def test_build_report_no_filters():
    scope = ScopeConfig(environment="dev")
    report = build_scope_report(PATHS, scope)
    assert len(report.allowed) == 4
    assert report.denied == []
    assert report.skipped == []
    assert report.total == 4


def test_build_report_with_deny():
    scope = ScopeConfig(environment="dev", denied_paths=["secret/legacy/*"])
    report = build_scope_report(PATHS, scope)
    assert "secret/legacy/old" in report.denied
    assert len(report.allowed) == 3


def test_build_report_strict_with_allow():
    scope = ScopeConfig(
        environment="prod",
        allowed_paths=["secret/app/*"],
        strict=True,
    )
    report = build_scope_report(PATHS, scope)
    assert set(report.allowed) == {"secret/app/db", "secret/app/cache"}
    assert "secret/legacy/old" in report.denied
    assert "secret/infra/tls" in report.denied


def test_build_report_strict_no_allow_list():
    scope = ScopeConfig(environment="prod", strict=True)
    report = build_scope_report(PATHS, scope)
    assert report.allowed == []
    assert report.denied == []
    assert len(report.skipped) == 4


def test_format_report_contains_environment():
    scope = ScopeConfig(environment="staging", denied_paths=["secret/legacy/*"])
    report = build_scope_report(PATHS, scope)
    text = format_scope_report(report)
    assert "staging" in text
    assert "Denied" in text
    assert "secret/legacy/old" in text


def test_format_report_no_denied_omits_section():
    scope = ScopeConfig(environment="dev")
    report = build_scope_report(PATHS, scope)
    text = format_scope_report(report)
    assert "Denied paths" not in text


def test_report_total_consistent():
    scope = ScopeConfig(
        environment="qa",
        allowed_paths=["secret/app/*"],
        denied_paths=["secret/legacy/*"],
        strict=True,
    )
    report = build_scope_report(PATHS, scope)
    assert report.total == len(PATHS)
