"""Tests for vaultpull.secret_group."""
import os
import pytest

from vaultpull.secret_group import GroupConfig, load_group_config, group_secrets


SECRETS = {
    "app/DB_HOST": "localhost",
    "app/DB_PASS": "secret",
    "infra/API_KEY": "key123",
    "STANDALONE": "value",
}


def test_load_defaults_no_section():
    cfg = load_group_config()
    assert cfg.enabled is False
    assert cfg.separator == "/"
    assert cfg.group_by_prefix is True
    assert cfg.default_group == "default"
    assert cfg.custom_groups == {}


def test_load_from_dict():
    cfg = load_group_config({"enabled": "true", "separator": ".", "default_group": "misc"})
    assert cfg.enabled is True
    assert cfg.separator == "."
    assert cfg.default_group == "misc"


def test_load_from_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_GROUP_ENABLED", "true")
    monkeypatch.setenv("VAULTPULL_GROUP_SEPARATOR", ":")
    cfg = load_group_config()
    assert cfg.enabled is True
    assert cfg.separator == ":"


def test_dict_overrides_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_GROUP_SEPARATOR", ":")
    cfg = load_group_config({"separator": "-"})
    assert cfg.separator == "-"


def test_group_by_prefix():
    cfg = GroupConfig(enabled=True, separator="/", group_by_prefix=True)
    result = group_secrets(SECRETS, cfg)
    assert "app" in result
    assert "infra" in result
    assert "app/DB_HOST" in result["app"]
    assert "app/DB_PASS" in result["app"]
    assert "infra/API_KEY" in result["infra"]


def test_no_separator_goes_to_default():
    cfg = GroupConfig(enabled=True, separator="/", group_by_prefix=True, default_group="default")
    result = group_secrets(SECRETS, cfg)
    assert "STANDALONE" in result.get("default", {})


def test_custom_groups_take_precedence():
    cfg = GroupConfig(
        enabled=True,
        separator="/",
        group_by_prefix=True,
        custom_groups={"database": ["app/DB"]},
    )
    result = group_secrets(SECRETS, cfg)
    assert "app/DB_HOST" in result["database"]
    assert "app/DB_PASS" in result["database"]
    # app group should not contain DB keys
    assert "app/DB_HOST" not in result.get("app", {})


def test_group_by_prefix_disabled():
    cfg = GroupConfig(enabled=True, separator="/", group_by_prefix=False, default_group="all")
    result = group_secrets(SECRETS, cfg)
    assert set(result.keys()) == {"all"}
    assert len(result["all"]) == len(SECRETS)


def test_empty_secrets():
    cfg = GroupConfig(enabled=True)
    result = group_secrets({}, cfg)
    assert result == {}
