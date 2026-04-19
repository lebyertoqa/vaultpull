"""Tests for vaultpull.filter."""

import pytest
from vaultpull.filter import FilterConfig, apply_filter, load_filter_config


SECRETS = {
    "APP_DB_HOST": "localhost",
    "APP_DB_PASS": "secret",
    "APP_API_KEY": "key123",
    "OTHER_VALUE": "other",
    "DEBUG": "true",
}


def test_load_defaults_no_section():
    cfg = load_filter_config()
    assert cfg.include_patterns == []
    assert cfg.exclude_patterns == []
    assert cfg.prefix_strip is None


def test_load_from_dict():
    cfg = load_filter_config({
        "include_patterns": "APP_*,DEBUG",
        "exclude_patterns": "APP_DB_*",
        "prefix_strip": "APP_",
    })
    assert cfg.include_patterns == ["APP_*", "DEBUG"]
    assert cfg.exclude_patterns == ["APP_DB_*"]
    assert cfg.prefix_strip == "APP_"


def test_load_list_values():
    cfg = load_filter_config({"include_patterns": ["APP_*", "DEBUG"]})
    assert cfg.include_patterns == ["APP_*", "DEBUG"]


def test_no_filters_returns_all():
    cfg = FilterConfig()
    result = apply_filter(SECRETS, cfg)
    assert result == SECRETS


def test_include_pattern():
    cfg = FilterConfig(include_patterns=["APP_*"])
    result = apply_filter(SECRETS, cfg)
    assert set(result.keys()) == {"APP_DB_HOST", "APP_DB_PASS", "APP_API_KEY"}


def test_exclude_pattern():
    cfg = FilterConfig(exclude_patterns=["APP_DB_*"])
    result = apply_filter(SECRETS, cfg)
    assert "APP_DB_HOST" not in result
    assert "APP_DB_PASS" not in result
    assert "APP_API_KEY" in result


def test_include_and_exclude():
    cfg = FilterConfig(include_patterns=["APP_*"], exclude_patterns=["APP_DB_*"])
    result = apply_filter(SECRETS, cfg)
    assert set(result.keys()) == {"APP_API_KEY"}


def test_prefix_strip():
    cfg = FilterConfig(include_patterns=["APP_*"], prefix_strip="APP_")
    result = apply_filter(SECRETS, cfg)
    assert "DB_HOST" in result
    assert "API_KEY" in result
    assert result["DB_HOST"] == "localhost"


def test_prefix_strip_empty_key_skipped():
    secrets = {"APP_": "val"}
    cfg = FilterConfig(prefix_strip="APP_")
    result = apply_filter(secrets, cfg)
    assert result == {}
