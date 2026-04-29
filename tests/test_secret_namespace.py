"""Tests for vaultpull.secret_namespace."""
import os
import pytest

from vaultpull.secret_namespace import (
    NamespaceConfig,
    load_namespace_config,
    extract_namespace,
    is_namespace_allowed,
    partition_secrets,
)


# ---------------------------------------------------------------------------
# load_namespace_config
# ---------------------------------------------------------------------------

def test_load_defaults_no_section():
    cfg = load_namespace_config()
    assert cfg.enabled is False
    assert cfg.default_namespace == "default"
    assert cfg.separator == "/"
    assert cfg.strip_namespace is True
    assert cfg.allowed_namespaces == []


def test_load_from_dict():
    cfg = load_namespace_config({
        "enabled": "true",
        "default_namespace": "prod",
        "separator": ":",
        "strip_namespace": "false",
        "allowed_namespaces": "prod,staging",
    })
    assert cfg.enabled is True
    assert cfg.default_namespace == "prod"
    assert cfg.separator == ":"
    assert cfg.strip_namespace is False
    assert cfg.allowed_namespaces == ["prod", "staging"]


def test_load_from_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_NS_ENABLED", "true")
    monkeypatch.setenv("VAULTPULL_NS_DEFAULT", "staging")
    monkeypatch.setenv("VAULTPULL_NS_SEPARATOR", "__")
    monkeypatch.setenv("VAULTPULL_NS_STRIP", "false")
    monkeypatch.setenv("VAULTPULL_NS_ALLOWED", "staging,dev")
    cfg = load_namespace_config()
    assert cfg.enabled is True
    assert cfg.default_namespace == "staging"
    assert cfg.separator == "__"
    assert cfg.strip_namespace is False
    assert cfg.allowed_namespaces == ["staging", "dev"]


def test_dict_overrides_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_NS_DEFAULT", "env-ns")
    cfg = load_namespace_config({"default_namespace": "dict-ns"})
    assert cfg.default_namespace == "dict-ns"


def test_allowed_namespaces_as_list():
    cfg = load_namespace_config({"allowed_namespaces": ["ns1", "ns2"]})
    assert cfg.allowed_namespaces == ["ns1", "ns2"]


# ---------------------------------------------------------------------------
# extract_namespace
# ---------------------------------------------------------------------------

def test_extract_namespace_with_separator():
    cfg = load_namespace_config({"separator": "/"})
    ns, key = extract_namespace("prod/DB_PASSWORD", cfg)
    assert ns == "prod"
    assert key == "DB_PASSWORD"


def test_extract_namespace_no_separator_uses_default():
    cfg = load_namespace_config({"default_namespace": "default"})
    ns, key = extract_namespace("DB_PASSWORD", cfg)
    assert ns == "default"
    assert key == "DB_PASSWORD"


# ---------------------------------------------------------------------------
# is_namespace_allowed
# ---------------------------------------------------------------------------

def test_is_namespace_allowed_empty_list_allows_all():
    cfg = load_namespace_config()
    assert is_namespace_allowed("anything", cfg) is True


def test_is_namespace_allowed_in_list():
    cfg = load_namespace_config({"allowed_namespaces": "prod,staging"})
    assert is_namespace_allowed("prod", cfg) is True
    assert is_namespace_allowed("dev", cfg) is False


# ---------------------------------------------------------------------------
# partition_secrets
# ---------------------------------------------------------------------------

def test_partition_secrets_strips_namespace():
    cfg = load_namespace_config({"separator": "/", "strip_namespace": "true"})
    secrets = {"prod/DB_HOST": "db.prod", "staging/DB_HOST": "db.staging"}
    result = partition_secrets(secrets, cfg)
    assert result["prod"] == {"DB_HOST": "db.prod"}
    assert result["staging"] == {"DB_HOST": "db.staging"}


def test_partition_secrets_keeps_namespace_prefix():
    cfg = load_namespace_config({"separator": "/", "strip_namespace": "false"})
    secrets = {"prod/API_KEY": "secret"}
    result = partition_secrets(secrets, cfg)
    assert result["prod"] == {"prod/API_KEY": "secret"}


def test_partition_secrets_filters_disallowed():
    cfg = load_namespace_config({"separator": "/", "allowed_namespaces": "prod"})
    secrets = {"prod/KEY": "v1", "dev/KEY": "v2"}
    result = partition_secrets(secrets, cfg)
    assert "dev" not in result
    assert result["prod"]["KEY"] == "v1"


def test_partition_secrets_no_separator_goes_to_default():
    cfg = load_namespace_config({"default_namespace": "global"})
    secrets = {"PLAIN_KEY": "value"}
    result = partition_secrets(secrets, cfg)
    assert result["global"] == {"PLAIN_KEY": "value"}
