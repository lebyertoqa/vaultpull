"""Tests for vaultpull.group_report."""
import pytest

from vaultpull.secret_group import GroupConfig
from vaultpull.group_report import GroupReport, build_group_report, format_group_report


SECRETS = {
    "app/DB_HOST": "localhost",
    "app/DB_PASS": "secret",
    "infra/API_KEY": "key123",
    "STANDALONE": "value",
}


@pytest.fixture
def default_cfg():
    return GroupConfig(enabled=True, separator="/", group_by_prefix=True)


def test_build_report_groups_by_prefix(default_cfg):
    report = build_group_report(SECRETS, default_cfg, environment="prod")
    assert report.environment == "prod"
    assert "app" in report.groups
    assert "infra" in report.groups
    assert report.total == len(SECRETS)


def test_build_report_total(default_cfg):
    report = build_group_report(SECRETS, default_cfg)
    assert report.total == 4


def test_build_report_group_count(default_cfg):
    report = build_group_report(SECRETS, default_cfg)
    # app, infra, default (STANDALONE)
    assert report.group_count >= 2


def test_build_report_empty_secrets(default_cfg):
    report = build_group_report({}, default_cfg)
    assert report.total == 0
    assert report.group_count == 0


def test_format_report_contains_environment(default_cfg):
    report = build_group_report(SECRETS, default_cfg, environment="staging")
    text = format_group_report(report)
    assert "staging" in text


def test_format_report_contains_group_names(default_cfg):
    report = build_group_report(SECRETS, default_cfg)
    text = format_group_report(report)
    assert "app" in text
    assert "infra" in text


def test_format_report_lists_keys(default_cfg):
    report = build_group_report(SECRETS, default_cfg)
    text = format_group_report(report)
    assert "app/DB_HOST" in text
    assert "infra/API_KEY" in text
