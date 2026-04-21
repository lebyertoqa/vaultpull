"""Tests for vaultpull/tag_report.py"""
import pytest
from vaultpull.secret_tags import TagConfig
from vaultpull.tag_report import build_tag_report, format_tag_report


SECRETS = {
    "db_pass": {"value": "hunter2", "tag:env": "prod"},
    "api_key": {"value": "abc123", "tag:env": "dev"},
    "plain":   {"value": "noop"},
}


def test_build_report_no_filters():
    cfg = TagConfig()
    report = build_tag_report(SECRETS, cfg, environment="test")
    assert report.total_input == 3
    assert report.total_passed == 3
    assert report.total_excluded == 0
    assert report.environment == "test"


def test_build_report_required_tag():
    cfg = TagConfig(required_tags=["env"])
    report = build_tag_report(SECRETS, cfg)
    assert report.total_passed == 2
    assert report.total_excluded == 1


def test_build_report_excluded_tag():
    cfg = TagConfig(excluded_tags=["env"])
    report = build_tag_report(SECRETS, cfg)
    assert report.total_passed == 1  # only 'plain' has no env tag


def test_build_report_strict():
    cfg = TagConfig(strict=True)
    report = build_tag_report(SECRETS, cfg)
    assert report.total_passed == 2
    assert report.total_excluded == 1
    assert report.strict is True


def test_format_report_contains_environment():
    cfg = TagConfig(required_tags=["env"])
    report = build_tag_report(SECRETS, cfg, environment="staging")
    text = format_tag_report(report)
    assert "staging" in text
    assert "Passed" in text
    assert "Excluded" in text


def test_format_report_shows_tags():
    cfg = TagConfig(required_tags=["env"], excluded_tags=["deprecated"])
    report = build_tag_report(SECRETS, cfg)
    text = format_tag_report(report)
    assert "env" in text
    assert "deprecated" in text


def test_format_report_strict_label():
    cfg = TagConfig(strict=True)
    report = build_tag_report(SECRETS, cfg)
    text = format_tag_report(report)
    assert "yes" in text
