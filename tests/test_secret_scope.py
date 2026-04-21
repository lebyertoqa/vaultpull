"""Tests for vaultpull.secret_scope."""

import os
import pytest

from vaultpull.secret_scope import (
    ScopeConfig,
    filter_paths,
    is_path_allowed,
    load_scope_config,
)


# ---------------------------------------------------------------------------
# load_scope_config
# ---------------------------------------------------------------------------

def test_load_defaults_no_section():
    cfg = load_scope_config({})
    assert cfg.environment == "default"
    assert cfg.allowed_paths == []
    assert cfg.denied_paths == []
    assert cfg.strict is False


def test_load_from_dict():
    cfg = load_scope_config({
        "environment": "production",
        "allowed_paths": "secret/app/*,secret/shared/*",
        "denied_paths": "secret/legacy/*",
        "strict": "true",
    })
    assert cfg.environment == "production"
    assert "secret/app/*" in cfg.allowed_paths
    assert "secret/shared/*" in cfg.allowed_paths
    assert cfg.denied_paths == ["secret/legacy/*"]
    assert cfg.strict is True


def test_load_from_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_ENVIRONMENT", "staging")
    monkeypatch.setenv("VAULTPULL_ALLOWED_PATHS", "secret/staging/*")
    monkeypatch.setenv("VAULTPULL_SCOPE_STRICT", "1")
    cfg = load_scope_config()
    assert cfg.environment == "staging"
    assert cfg.allowed_paths == ["secret/staging/*"]
    assert cfg.strict is True


# ---------------------------------------------------------------------------
# is_path_allowed
# ---------------------------------------------------------------------------

def test_no_filters_allows_all():
    scope = ScopeConfig(environment="dev")
    assert is_path_allowed("secret/anything", scope) is True


def test_denied_path_blocked():
    scope = ScopeConfig(environment="dev", denied_paths=["secret/legacy/*"])
    assert is_path_allowed("secret/legacy/db", scope) is False
    assert is_path_allowed("secret/app/db", scope) is True


def test_allowed_path_wildcard():
    scope = ScopeConfig(environment="dev", allowed_paths=["secret/app/*"])
    assert is_path_allowed("secret/app/db", scope) is True
    assert is_path_allowed("secret/other/db", scope) is False


def test_strict_mode_no_allow_list_blocks_all():
    scope = ScopeConfig(environment="prod", strict=True)
    assert is_path_allowed("secret/anything", scope) is False


def test_strict_mode_with_allow_list():
    scope = ScopeConfig(environment="prod", allowed_paths=["secret/prod/*"], strict=True)
    assert is_path_allowed("secret/prod/key", scope) is True
    assert is_path_allowed("secret/dev/key", scope) is False


def test_deny_takes_priority_over_allow():
    scope = ScopeConfig(
        environment="prod",
        allowed_paths=["secret/*"],
        denied_paths=["secret/legacy/*"],
    )
    assert is_path_allowed("secret/app/key", scope) is True
    assert is_path_allowed("secret/legacy/key", scope) is False


# ---------------------------------------------------------------------------
# filter_paths
# ---------------------------------------------------------------------------

def test_filter_paths_removes_denied():
    scope = ScopeConfig(environment="dev", denied_paths=["secret/legacy/*"])
    paths = ["secret/app/db", "secret/legacy/old", "secret/shared/token"]
    result = filter_paths(paths, scope)
    assert "secret/legacy/old" not in result
    assert len(result) == 2


def test_filter_paths_empty_input():
    scope = ScopeConfig(environment="dev")
    assert filter_paths([], scope) == []
