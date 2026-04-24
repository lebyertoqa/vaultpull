"""Tests for vaultpull.secret_expiry and vaultpull.expiry_config_loader."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from vaultpull.secret_expiry import (
    ExpiryConfig,
    ExpiryRecord,
    build_expiry_report,
    format_expiry_report,
    load_expiry_config,
)
from vaultpull.expiry_config_loader import (
    describe_expiry,
    extract_expiry_section,
    get_expiry_config,
)


# ---------------------------------------------------------------------------
# load_expiry_config
# ---------------------------------------------------------------------------

def test_load_defaults_no_section():
    cfg = load_expiry_config()
    assert cfg.warn_before_days == 7
    assert cfg.fail_on_expired is False
    assert cfg.enabled is True


def test_load_from_dict():
    cfg = load_expiry_config({"warn_before_days": "3", "fail_on_expired": "true", "enabled": "false"})
    assert cfg.warn_before_days == 3
    assert cfg.fail_on_expired is True
    assert cfg.enabled is False


def test_load_from_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_EXPIRY_WARN_DAYS", "14")
    monkeypatch.setenv("VAULTPULL_EXPIRY_FAIL", "true")
    cfg = load_expiry_config()
    assert cfg.warn_before_days == 14
    assert cfg.fail_on_expired is True


def test_dict_overrides_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_EXPIRY_WARN_DAYS", "30")
    cfg = load_expiry_config({"warn_before_days": "2"})
    assert cfg.warn_before_days == 2


# ---------------------------------------------------------------------------
# ExpiryRecord helpers
# ---------------------------------------------------------------------------

def test_is_expired_true():
    past = datetime.now(timezone.utc) - timedelta(days=1)
    rec = ExpiryRecord(key="OLD_TOKEN", expires_at=past, ttl_seconds=0)
    assert rec.is_expired is True


def test_is_expired_false():
    future = datetime.now(timezone.utc) + timedelta(days=10)
    rec = ExpiryRecord(key="FRESH_TOKEN", expires_at=future, ttl_seconds=864000)
    assert rec.is_expired is False


def test_is_expired_no_expiry():
    rec = ExpiryRecord(key="NO_TTL", expires_at=None, ttl_seconds=None)
    assert rec.is_expired is False
    assert rec.days_until_expiry() is None


def test_days_until_expiry():
    future = datetime.now(timezone.utc) + timedelta(days=5)
    rec = ExpiryRecord(key="K", expires_at=future, ttl_seconds=432000)
    days = rec.days_until_expiry()
    assert days is not None
    assert 4.9 < days < 5.1


# ---------------------------------------------------------------------------
# build_expiry_report
# ---------------------------------------------------------------------------

def test_build_report_no_records():
    cfg = ExpiryConfig()
    report = build_expiry_report("prod", [], cfg)
    assert report.environment == "prod"
    assert report.expired == []
    assert report.expiring_soon == []


def test_build_report_with_expired():
    cfg = ExpiryConfig(warn_before_days=7)
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    records = [ExpiryRecord(key="OLD", expires_at=past, ttl_seconds=0)]
    report = build_expiry_report("staging", records, cfg)
    assert "OLD" in report.expired
    assert report.expiring_soon == []


def test_build_report_expiring_soon():
    cfg = ExpiryConfig(warn_before_days=7)
    soon = datetime.now(timezone.utc) + timedelta(days=3)
    records = [ExpiryRecord(key="SOON", expires_at=soon, ttl_seconds=259200)]
    report = build_expiry_report("dev", records, cfg)
    assert "SOON" in report.expiring_soon
    assert report.expired == []


def test_format_report_contains_environment():
    cfg = ExpiryConfig()
    report = build_expiry_report("prod", [], cfg)
    text = format_expiry_report(report)
    assert "prod" in text
    assert "Expiry Report" in text


# ---------------------------------------------------------------------------
# expiry_config_loader
# ---------------------------------------------------------------------------

def test_extract_expiry_section_present():
    config = {"expiry": {"warn_before_days": "5"}}
    section = extract_expiry_section(config)
    assert section == {"warn_before_days": "5"}


def test_extract_expiry_section_missing():
    assert extract_expiry_section({}) is None


def test_get_expiry_config_full():
    config = {"expiry": {"warn_before_days": "10", "fail_on_expired": "true"}}
    cfg = get_expiry_config(config)
    assert cfg.warn_before_days == 10
    assert cfg.fail_on_expired is True


def test_describe_expiry():
    cfg = ExpiryConfig(warn_before_days=3, fail_on_expired=True, enabled=False)
    desc = describe_expiry(cfg)
    assert "warn_before_days=3" in desc
    assert "fail_on_expired=True" in desc
    assert "enabled=False" in desc
