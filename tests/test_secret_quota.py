"""Tests for vaultpull.secret_quota."""
import os
import pytest

from vaultpull.secret_quota import (
    QuotaConfig,
    QuotaViolation,
    check_quota,
    load_quota_config,
)


# ---------------------------------------------------------------------------
# load_quota_config
# ---------------------------------------------------------------------------

def test_load_defaults_no_section():
    cfg = load_quota_config()
    assert cfg.max_secrets == 0
    assert cfg.max_per_path == 0
    assert cfg.warn_threshold == 0
    assert cfg.strict is False


def test_load_from_dict():
    cfg = load_quota_config({"max_secrets": "10", "max_per_path": "3", "warn_threshold": "8", "strict": "true"})
    assert cfg.max_secrets == 10
    assert cfg.max_per_path == 3
    assert cfg.warn_threshold == 8
    assert cfg.strict is True


def test_load_from_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_QUOTA_MAX_SECRETS", "20")
    monkeypatch.setenv("VAULTPULL_QUOTA_MAX_PER_PATH", "5")
    monkeypatch.setenv("VAULTPULL_QUOTA_WARN_THRESHOLD", "15")
    monkeypatch.setenv("VAULTPULL_QUOTA_STRICT", "true")
    cfg = load_quota_config()
    assert cfg.max_secrets == 20
    assert cfg.max_per_path == 5
    assert cfg.warn_threshold == 15
    assert cfg.strict is True


def test_dict_takes_precedence_over_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_QUOTA_MAX_SECRETS", "99")
    cfg = load_quota_config({"max_secrets": "7"})
    assert cfg.max_secrets == 7


def test_invalid_int_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("VAULTPULL_QUOTA_MAX_SECRETS", "not_a_number")
    cfg = load_quota_config()
    assert cfg.max_secrets == 0


# ---------------------------------------------------------------------------
# check_quota
# ---------------------------------------------------------------------------

def _secrets(n: int):
    return {f"KEY_{i}": f"val{i}" for i in range(n)}


def test_no_violations_when_unlimited():
    cfg = QuotaConfig()
    report = check_quota(_secrets(100), cfg)
    assert not report.has_violations
    assert report.total == 100


def test_global_quota_breach():
    cfg = QuotaConfig(max_secrets=5)
    report = check_quota(_secrets(6), cfg)
    assert report.has_violations
    assert report.violations[0].kind == "global"
    assert report.violations[0].count == 6
    assert report.violations[0].limit == 5


def test_global_quota_exact_limit_no_breach():
    cfg = QuotaConfig(max_secrets=5)
    report = check_quota(_secrets(5), cfg)
    assert not report.has_violations


def test_per_path_breach():
    secrets = {"db/HOST": "h", "db/PORT": "5432", "db/PASS": "x", "app/KEY": "k"}
    cfg = QuotaConfig(max_per_path=2)
    report = check_quota(secrets, cfg)
    assert report.has_violations
    paths = [v.path for v in report.violations]
    assert "db" in paths


def test_warn_threshold_no_violation():
    cfg = QuotaConfig(max_secrets=10, warn_threshold=3)
    report = check_quota(_secrets(4), cfg)
    assert not report.has_violations
    assert len(report.warnings) == 1
    assert "warn threshold" in report.warnings[0]


def test_warn_threshold_suppressed_when_violation_present():
    cfg = QuotaConfig(max_secrets=3, warn_threshold=2)
    report = check_quota(_secrets(5), cfg)
    assert report.has_violations
    assert report.warnings == []


def test_violation_message_contains_details():
    v = QuotaViolation(kind="global", path="root", count=10, limit=5)
    assert "global" in v.message
    assert "10" in v.message
    assert "5" in v.message
