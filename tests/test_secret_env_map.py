"""Tests for vaultpull.secret_env_map."""
import pytest

from vaultpull.secret_env_map import (
    EnvMapConfig,
    _split_pairs,
    apply_env_prefix,
    load_env_map_config,
    map_secrets,
)


def test_split_pairs_basic():
    result = _split_pairs("secret/app=APP,secret/db=DB")
    assert result == {"secret/app": "APP", "secret/db": "DB"}


def test_split_pairs_empty():
    assert _split_pairs("") == {}


def test_load_defaults_no_section():
    cfg = load_env_map_config()
    assert cfg.mappings == {}
    assert cfg.strip_prefix is True
    assert cfg.uppercase is True


def test_load_from_dict():
    cfg = load_env_map_config(
        {"mappings": "secret/app=APP", "strip_prefix": "false", "uppercase": "false"}
    )
    assert cfg.mappings == {"secret/app": "APP"}
    assert cfg.strip_prefix is False
    assert cfg.uppercase is False


def test_load_from_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_ENV_MAPPINGS", "secret/svc=SVC")
    cfg = load_env_map_config()
    assert cfg.mappings == {"secret/svc": "SVC"}


def test_dict_overrides_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_ENV_MAPPINGS", "secret/svc=SVC")
    cfg = load_env_map_config({"mappings": "secret/app=APP"})
    assert cfg.mappings == {"secret/app": "APP"}


def test_apply_env_prefix_with_mapping():
    cfg = EnvMapConfig(mappings={"secret/app": "APP"}, strip_prefix=False, uppercase=True)
    result = apply_env_prefix("db_pass", "secret/app", cfg)
    assert result == "APP_DB_PASS"


def test_apply_env_prefix_strip_path_segment():
    cfg = EnvMapConfig(mappings={}, strip_prefix=True, uppercase=True)
    result = apply_env_prefix("secret/app/db_pass", "secret/app", cfg)
    assert result == "DB_PASS"


def test_apply_env_prefix_no_mapping_no_strip():
    cfg = EnvMapConfig(mappings={}, strip_prefix=False, uppercase=True)
    result = apply_env_prefix("db_pass", "secret/app", cfg)
    assert result == "DB_PASS"


def test_map_secrets_renames_keys():
    cfg = EnvMapConfig(mappings={"secret/app": "APP"}, strip_prefix=False, uppercase=True)
    result = map_secrets({"db_host": "localhost", "db_port": "5432"}, "secret/app", cfg)
    assert result == {"APP_DB_HOST": "localhost", "APP_DB_PORT": "5432"}


def test_map_secrets_no_mapping():
    cfg = EnvMapConfig(mappings={}, strip_prefix=False, uppercase=True)
    result = map_secrets({"key": "val"}, "secret/app", cfg)
    assert result == {"KEY": "val"}
