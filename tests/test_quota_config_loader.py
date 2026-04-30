"""Tests for vaultpull.quota_config_loader."""
import pytest

from vaultpull.quota_config_loader import describe_quota, extract_quota_section, get_quota_config
from vaultpull.secret_quota import QuotaConfig


def test_extract_quota_section_present():
    config = {"quota": {"max_secrets": "5"}}
    assert extract_quota_section(config) == {"max_secrets": "5"}


def test_extract_quota_section_missing():
    assert extract_quota_section({}) is None


def test_extract_quota_section_uppercase_key():
    config = {"QUOTA": {"max_secrets": "3"}}
    assert extract_quota_section(config) == {"max_secrets": "3"}


def test_get_quota_config_from_dict():
    config = {"quota": {"max_secrets": "10", "strict": "true"}}
    cfg = get_quota_config(config)
    assert cfg.max_secrets == 10
    assert cfg.strict is True


def test_get_quota_config_no_section():
    cfg = get_quota_config({})
    assert isinstance(cfg, QuotaConfig)
    assert cfg.max_secrets == 0


def test_describe_quota_unlimited():
    cfg = QuotaConfig()
    assert describe_quota(cfg) == "quota(unlimited)"


def test_describe_quota_with_limits():
    cfg = QuotaConfig(max_secrets=50, max_per_path=10)
    desc = describe_quota(cfg)
    assert "max_secrets=50" in desc
    assert "max_per_path=10" in desc


def test_describe_quota_strict_flag():
    cfg = QuotaConfig(strict=True)
    assert "strict=true" in describe_quota(cfg)


def test_describe_quota_warn_threshold():
    cfg = QuotaConfig(warn_threshold=40)
    assert "warn_threshold=40" in describe_quota(cfg)
