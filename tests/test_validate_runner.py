"""Tests for vaultpull.validate_runner — run_validation and format_validation_report."""

import pytest

from vaultpull.validate_runner import run_validation, format_validation_report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cfg_section(required=None, forbidden=None, pattern=None):
    """Build a minimal config dict with a [validate] section."""
    section = {}
    if required is not None:
        section["required"] = ",".join(required)
    if forbidden is not None:
        section["forbidden"] = ",".join(forbidden)
    if pattern is not None:
        section["pattern"] = pattern
    return {"validate": section}


# ---------------------------------------------------------------------------
# run_validation
# ---------------------------------------------------------------------------

def test_run_validation_all_pass():
    secrets = {"DB_HOST": "localhost", "DB_PORT": "5432"}
    cfg = _cfg_section(required=["DB_HOST", "DB_PORT"])
    result = run_validation(secrets, cfg)
    assert result.passed is True
    assert result.missing == []
    assert result.forbidden == []
    assert result.pattern_failures == []


def test_run_validation_missing_required():
    secrets = {"DB_HOST": "localhost"}
    cfg = _cfg_section(required=["DB_HOST", "DB_PORT", "DB_NAME"])
    result = run_validation(secrets, cfg)
    assert result.passed is False
    assert "DB_PORT" in result.missing
    assert "DB_NAME" in result.missing


def test_run_validation_forbidden_present():
    secrets = {"DEBUG": "true", "APP_KEY": "abc"}
    cfg = _cfg_section(forbidden=["DEBUG", "TEST_MODE"])
    result = run_validation(secrets, cfg)
    assert result.passed is False
    assert "DEBUG" in result.forbidden
    assert "TEST_MODE" not in result.forbidden  # not present, so not flagged


def test_run_validation_pattern_failure():
    secrets = {"PORT": "not-a-number"}
    cfg = _cfg_section(pattern=r"^\d+$")
    result = run_validation(secrets, cfg)
    assert result.passed is False
    assert "PORT" in result.pattern_failures


def test_run_validation_pattern_pass():
    secrets = {"PORT": "8080", "TIMEOUT": "30"}
    cfg = _cfg_section(pattern=r"^\d+$")
    result = run_validation(secrets, cfg)
    assert result.passed is True
    assert result.pattern_failures == []


def test_run_validation_no_section():
    """No [validate] section — everything should pass with empty rules."""
    secrets = {"FOO": "bar"}
    result = run_validation(secrets, {})
    assert result.passed is True


def test_run_validation_empty_secrets():
    secrets = {}
    cfg = _cfg_section(required=["API_KEY"])
    result = run_validation(secrets, cfg)
    assert result.passed is False
    assert "API_KEY" in result.missing


# ---------------------------------------------------------------------------
# format_validation_report
# ---------------------------------------------------------------------------

def test_format_report_all_pass():
    secrets = {"DB_HOST": "localhost"}
    cfg = _cfg_section(required=["DB_HOST"])
    result = run_validation(secrets, cfg)
    report = format_validation_report(result)
    assert "PASSED" in report or "passed" in report.lower()


def test_format_report_missing_keys():
    secrets = {}
    cfg = _cfg_section(required=["DB_HOST", "DB_PASS"])
    result = run_validation(secrets, cfg)
    report = format_validation_report(result)
    assert "DB_HOST" in report
    assert "DB_PASS" in report
    assert "missing" in report.lower()


def test_format_report_forbidden_keys():
    secrets = {"DEBUG": "1"}
    cfg = _cfg_section(forbidden=["DEBUG"])
    result = run_validation(secrets, cfg)
    report = format_validation_report(result)
    assert "DEBUG" in report
    assert "forbidden" in report.lower()


def test_format_report_pattern_failures():
    secrets = {"PORT": "abc"}
    cfg = _cfg_section(pattern=r"^\d+$")
    result = run_validation(secrets, cfg)
    report = format_validation_report(result)
    assert "PORT" in report
    assert "pattern" in report.lower()


def test_format_report_is_string():
    result = run_validation({}, {})
    report = format_validation_report(result)
    assert isinstance(report, str)
    assert len(report) > 0
