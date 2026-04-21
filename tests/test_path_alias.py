"""Tests for vaultpull/path_alias.py"""
import os
import pytest
from vaultpull.path_alias import (
    AliasConfig,
    load_alias_config,
    resolve_key,
    apply_aliases,
    _split_pairs,
)


def test_split_pairs_basic():
    result = _split_pairs("secret/app=APP,secret/db=DB")
    assert result == {"secret/app": "APP", "secret/db": "DB"}


def test_split_pairs_empty():
    assert _split_pairs("") == {}


def test_load_defaults_no_section():
    cfg = load_alias_config()
    assert cfg.aliases == {}
    assert cfg.strip_prefix is True
    assert cfg.uppercase is True


def test_load_from_dict():
    cfg = load_alias_config({"aliases": {"secret/app": "MYAPP"}, "strip_prefix": "false", "uppercase": "false"})
    assert cfg.aliases == {"secret/app": "MYAPP"}
    assert cfg.strip_prefix is False
    assert cfg.uppercase is False


def test_load_aliases_from_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_ALIASES", "secret/svc=SVC")
    cfg = load_alias_config()
    assert cfg.aliases == {"secret/svc": "SVC"}


def test_resolve_key_with_alias():
    cfg = AliasConfig(aliases={"secret/app": "APP"}, strip_prefix=True, uppercase=True)
    assert resolve_key("secret/app", "db_pass", cfg) == "APP_DB_PASS"


def test_resolve_key_no_alias_strip_prefix():
    cfg = AliasConfig(aliases={}, strip_prefix=True, uppercase=True)
    # strip_prefix=True means no prefix added from path
    assert resolve_key("secret/app", "api_key", cfg) == "API_KEY"


def test_resolve_key_no_alias_no_strip():
    cfg = AliasConfig(aliases={}, strip_prefix=False, uppercase=True)
    assert resolve_key("secret/app", "token", cfg) == "APP_TOKEN"


def test_resolve_key_lowercase_disabled():
    cfg = AliasConfig(aliases={"secret/svc": "svc"}, strip_prefix=True, uppercase=False)
    assert resolve_key("secret/svc", "key", cfg) == "svc_key"


def test_apply_aliases_renames_all():
    cfg = AliasConfig(aliases={"secret/db": "DATABASE"}, strip_prefix=True, uppercase=True)
    secrets = {"host": "localhost", "port": "5432"}
    result = apply_aliases(secrets, "secret/db", cfg)
    assert result == {"DATABASE_HOST": "localhost", "DATABASE_PORT": "5432"}


def test_apply_aliases_empty_secrets():
    cfg = AliasConfig(aliases={}, strip_prefix=True, uppercase=True)
    assert apply_aliases({}, "secret/x", cfg) == {}
