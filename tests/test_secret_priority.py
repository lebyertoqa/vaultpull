"""Tests for vaultpull.secret_priority."""
import pytest

from vaultpull.secret_priority import (
    PriorityConfig,
    build_priority_report,
    format_priority_report,
    load_priority_config,
    score_secret,
)


# ---------------------------------------------------------------------------
# load_priority_config
# ---------------------------------------------------------------------------

def test_load_defaults_no_section():
    cfg = load_priority_config()
    assert "password" in cfg.high_keywords
    assert "api" in cfg.medium_keywords
    assert cfg.pinned_keys == []


def test_load_from_dict():
    cfg = load_priority_config({"high_keywords": "secret,token", "pinned_keys": "MASTER_KEY"})
    assert cfg.high_keywords == ["secret", "token"]
    assert cfg.pinned_keys == ["MASTER_KEY"]


def test_load_empty_medium_keywords():
    cfg = load_priority_config({"medium_keywords": ""})
    assert cfg.medium_keywords == []


# ---------------------------------------------------------------------------
# score_secret
# ---------------------------------------------------------------------------

def test_score_pinned_key():
    cfg = load_priority_config({"pinned_keys": "CRITICAL"})
    assert score_secret("CRITICAL", cfg) == 100


def test_score_high_keyword():
    cfg = load_priority_config()
    assert score_secret("DB_PASSWORD", cfg) == 80


def test_score_medium_keyword():
    cfg = load_priority_config()
    assert score_secret("API_ENDPOINT", cfg) == 50


def test_score_low_priority():
    cfg = load_priority_config()
    assert score_secret("REGION", cfg) == 10


def test_score_case_insensitive():
    cfg = load_priority_config()
    assert score_secret("db_Token", cfg) == 80


# ---------------------------------------------------------------------------
# build_priority_report
# ---------------------------------------------------------------------------

def test_build_report_order():
    secrets = {"REGION": "us-east-1", "DB_PASSWORD": "s3cr3t", "API_KEY": "abc"}
    cfg = load_priority_config()
    report = build_priority_report(secrets, cfg, environment="prod")
    keys_in_order = [k for k, _ in report.ordered]
    assert keys_in_order.index("DB_PASSWORD") < keys_in_order.index("API_KEY")
    assert keys_in_order.index("API_KEY") < keys_in_order.index("REGION")


def test_build_report_environment_label():
    report = build_priority_report({"X": "1"}, load_priority_config(), environment="staging")
    assert report.environment == "staging"


def test_build_report_empty_secrets():
    report = build_priority_report({}, load_priority_config())
    assert report.scores == {}
    assert report.ordered == []


# ---------------------------------------------------------------------------
# format_priority_report
# ---------------------------------------------------------------------------

def test_format_report_contains_environment():
    secrets = {"DB_PASSWORD": "x"}
    report = build_priority_report(secrets, load_priority_config(), environment="dev")
    text = format_priority_report(report)
    assert "dev" in text
    assert "HIGH" in text


def test_format_report_low_label():
    secrets = {"REGION": "us-east-1"}
    report = build_priority_report(secrets, load_priority_config())
    text = format_priority_report(report)
    assert "LOW" in text
