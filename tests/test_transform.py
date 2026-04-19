"""Tests for vaultpull.transform."""

import pytest
from vaultpull.transform import (
    TransformConfig,
    load_transform_config,
    apply_transform,
)


def test_load_defaults_no_section():
    cfg = load_transform_config()
    assert cfg.prefix == ""
    assert cfg.uppercase is True
    assert cfg.strip_path is True
    assert cfg.key_map == {}


def test_load_from_dict():
    cfg = load_transform_config({"prefix": "APP_", "uppercase": "false", "strip_path": "false"})
    assert cfg.prefix == "APP_"
    assert cfg.uppercase is False
    assert cfg.strip_path is False


def test_load_key_map():
    cfg = load_transform_config({"key_map": {"DB_PASS": "DATABASE_PASSWORD"}})
    assert cfg.key_map == {"DB_PASS": "DATABASE_PASSWORD"}


def test_normalize_strips_path():
    secrets = {"secret/app/db_password": "hunter2"}
    cfg = TransformConfig(strip_path=True, uppercase=True)
    result = apply_transform(secrets, cfg)
    assert "DB_PASSWORD" in result
    assert result["DB_PASSWORD"] == "hunter2"


def test_normalize_no_strip_path():
    secrets = {"secret/app/db_password": "hunter2"}
    cfg = TransformConfig(strip_path=False, uppercase=True)
    result = apply_transform(secrets, cfg)
    assert "SECRET_APP_DB_PASSWORD" in result


def test_uppercase_false():
    secrets = {"api_key": "abc123"}
    cfg = TransformConfig(uppercase=False)
    result = apply_transform(secrets, cfg)
    assert "api_key" in result


def test_prefix_applied():
    secrets = {"token": "xyz"}
    cfg = TransformConfig(prefix="MYAPP_", uppercase=True)
    result = apply_transform(secrets, cfg)
    assert "MYAPP_TOKEN" in result
    assert result["MYAPP_TOKEN"] == "xyz"


def test_key_map_override():
    secrets = {"db_pass": "secret"}
    cfg = TransformConfig(uppercase=True, key_map={"DB_PASS": "DATABASE_PASSWORD"})
    result = apply_transform(secrets, cfg)
    assert "DATABASE_PASSWORD" in result
    assert "DB_PASS" not in result


def test_special_chars_replaced():
    secrets = {"my-key.name": "value"}
    cfg = TransformConfig(strip_path=False, uppercase=True)
    result = apply_transform(secrets, cfg)
    assert "MY_KEY_NAME" in result


def test_empty_secrets():
    result = apply_transform({}, TransformConfig())
    assert result == {}
