"""Tests for secret dependency tracking and validation."""
import pytest

from vaultpull.secret_dependencies import (
    DependencyConfig,
    DependencyViolation,
    check_dependencies,
    load_dependency_config,
)
from vaultpull.dependency_report import (
    build_dependency_report,
    describe_dependencies,
    format_dependency_report,
)


# ---------------------------------------------------------------------------
# load_dependency_config
# ---------------------------------------------------------------------------

def test_load_defaults_no_section():
    cfg = load_dependency_config()
    assert cfg.requires == {}
    assert cfg.conflicts == {}
    assert cfg.groups == {}
    assert cfg.strict is False


def test_load_from_dict():
    cfg = load_dependency_config({
        "requires.DB_PASSWORD": "DB_HOST, DB_PORT",
        "conflicts.DEBUG": "PRODUCTION",
        "group.database": "DB_HOST, DB_PORT, DB_PASSWORD",
        "strict": "true",
    })
    assert cfg.requires == {"DB_PASSWORD": ["DB_HOST", "DB_PORT"]}
    assert cfg.conflicts == {"DEBUG": ["PRODUCTION"]}
    assert cfg.groups == {"database": ["DB_HOST", "DB_PORT", "DB_PASSWORD"]}
    assert cfg.strict is True


def test_load_ignores_unknown_keys():
    cfg = load_dependency_config({"unknown_key": "value"})
    assert cfg.requires == {}
    assert cfg.conflicts == {}


# ---------------------------------------------------------------------------
# check_dependencies — requires
# ---------------------------------------------------------------------------

def test_no_violations_when_all_present():
    cfg = load_dependency_config({"requires.DB_PASSWORD": "DB_HOST"})
    secrets = {"DB_PASSWORD": "s3cr3t", "DB_HOST": "localhost"}
    report = check_dependencies(secrets, cfg)
    assert not report.has_violations
    assert report.checked_keys == 2


def test_missing_dependency_raises_violation():
    cfg = load_dependency_config({"requires.DB_PASSWORD": "DB_HOST, DB_PORT"})
    secrets = {"DB_PASSWORD": "s3cr3t", "DB_HOST": "localhost"}  # DB_PORT missing
    report = check_dependencies(secrets, cfg)
    assert report.has_violations
    kinds = [v.kind for v in report.violations]
    assert "missing_dependency" in kinds


def test_no_violation_when_key_itself_absent():
    """If the key that has a 'requires' rule is not present, no violation."""
    cfg = load_dependency_config({"requires.DB_PASSWORD": "DB_HOST"})
    secrets = {"API_KEY": "abc"}  # DB_PASSWORD not present
    report = check_dependencies(secrets, cfg)
    assert not report.has_violations


# ---------------------------------------------------------------------------
# check_dependencies — conflicts
# ---------------------------------------------------------------------------

def test_conflict_violation_when_both_present():
    cfg = load_dependency_config({"conflicts.DEBUG": "PRODUCTION"})
    secrets = {"DEBUG": "true", "PRODUCTION": "true"}
    report = check_dependencies(secrets, cfg)
    assert report.has_violations
    assert report.violations[0].kind == "conflict"


def test_no_conflict_when_only_one_present():
    cfg = load_dependency_config({"conflicts.DEBUG": "PRODUCTION"})
    secrets = {"DEBUG": "true"}
    report = check_dependencies(secrets, cfg)
    assert not report.has_violations


# ---------------------------------------------------------------------------
# check_dependencies — groups
# ---------------------------------------------------------------------------

def test_incomplete_group_violation():
    cfg = load_dependency_config({"group.database": "DB_HOST, DB_PORT, DB_PASSWORD"})
    secrets = {"DB_HOST": "localhost", "DB_PORT": "5432"}  # DB_PASSWORD missing
    report = check_dependencies(secrets, cfg)
    assert report.has_violations
    assert report.violations[0].kind == "incomplete_group"
    assert "DB_PASSWORD" in report.violations[0].detail


def test_complete_group_no_violation():
    cfg = load_dependency_config({"group.database": "DB_HOST, DB_PORT"})
    secrets = {"DB_HOST": "localhost", "DB_PORT": "5432"}
    report = check_dependencies(secrets, cfg)
    assert not report.has_violations


def test_group_not_triggered_when_none_present():
    cfg = load_dependency_config({"group.database": "DB_HOST, DB_PORT"})
    secrets = {"API_KEY": "abc"}  # none of the group keys present
    report = check_dependencies(secrets, cfg)
    assert not report.has_violations


# ---------------------------------------------------------------------------
# build_dependency_report / format_dependency_report
# ---------------------------------------------------------------------------

def test_build_report_structure():
    cfg = load_dependency_config({"requires.DB_PASSWORD": "DB_HOST"})
    secrets = {"DB_PASSWORD": "x"}  # DB_HOST missing
    result = build_dependency_report(secrets, cfg, environment="staging")
    assert result["environment"] == "staging"
    assert result["has_violations"] is True
    assert result["violation_count"] == 1
    assert result["violations"][0]["kind"] == "missing_dependency"


def test_format_report_contains_environment():
    cfg = load_dependency_config()
    result = build_dependency_report({}, cfg, environment="production")
    text = format_dependency_report(result)
    assert "production" in text


def test_format_report_lists_violations():
    cfg = load_dependency_config({"conflicts.A": "B"})
    secrets = {"A": "1", "B": "2"}
    result = build_dependency_report(secrets, cfg)
    text = format_dependency_report(result)
    assert "conflict" in text


# ---------------------------------------------------------------------------
# describe_dependencies
# ---------------------------------------------------------------------------

def test_describe_no_rules():
    cfg = DependencyConfig()
    assert describe_dependencies(cfg) == "no dependency rules configured"


def test_describe_with_rules():
    cfg = load_dependency_config({
        "requires.A": "B",
        "conflicts.C": "D",
        "strict": "true",
    })
    desc = describe_dependencies(cfg)
    assert "require rule" in desc
    assert "conflict rule" in desc
    assert "strict" in desc
