"""Tests for vaultpull.secret_lint."""
import pytest
from vaultpull.secret_lint import (
    lint_secrets,
    format_lint_report,
    LintIssue,
    LintReport,
)


def test_no_issues_for_clean_secrets():
    secrets = {"DATABASE_URL": "postgres://host/db", "API_KEY": "supersecretvalue123"}
    report = lint_secrets(secrets, environment="prod")
    assert not report.issues
    assert not report.has_errors


def test_empty_value_raises_error():
    report = lint_secrets({"MY_KEY": ""}, environment="prod")
    errors = report.errors
    assert len(errors) == 1
    assert errors[0].severity == "error"
    assert "empty" in errors[0].message


def test_weak_value_raises_warning():
    report = lint_secrets({"DB_PASSWORD": "password"}, environment="prod")
    warnings = report.warnings
    assert any("weak" in w.message.lower() or "placeholder" in w.message.lower() for w in warnings)


def test_short_value_raises_warning():
    report = lint_secrets({"TOKEN": "abc"}, environment="dev")
    assert report.warnings  # short value triggers weak check


def test_key_convention_warning_for_lowercase():
    report = lint_secrets({"my_key": "somevalue"}, environment="dev")
    warnings = report.warnings
    assert any("UPPER_SNAKE_CASE" in w.message for w in warnings)


def test_key_convention_ok_for_uppercase():
    report = lint_secrets({"MY_KEY_123": "somevalue"}, environment="dev")
    # no convention warning
    convention_warns = [w for w in report.warnings if "convention" in w.message.lower()]
    assert not convention_warns


def test_multiple_issues_reported():
    secrets = {"bad-key": "", "WEAK": "test"}
    report = lint_secrets(secrets)
    assert len(report.issues) >= 2


def test_has_errors_true_when_empty_value():
    report = lint_secrets({"SECRET": ""})
    assert report.has_errors


def test_has_errors_false_when_only_warnings():
    report = lint_secrets({"my_key": "somereasonablylargevalue"})
    # may have convention warning but no error
    assert not report.has_errors


def test_format_lint_report_no_issues():
    report = LintReport(environment="staging")
    output = format_lint_report(report)
    assert "No issues" in output
    assert "staging" in output


def test_format_lint_report_with_issues():
    report = LintReport(environment="prod", issues=[
        LintIssue(key="X", severity="error", message="empty value"),
        LintIssue(key="Y", severity="warning", message="weak value"),
    ])
    output = format_lint_report(report)
    assert "[ERROR]" in output
    assert "[WARN]" in output
    assert "1 error" in output
    assert "1 warning" in output
