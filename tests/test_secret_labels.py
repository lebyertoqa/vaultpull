"""Tests for vaultpull.secret_labels."""
import pytest
from vaultpull.secret_labels import (
    LabelConfig,
    _split_pairs,
    apply_labels,
    load_label_config,
)


# ---------------------------------------------------------------------------
# _split_pairs
# ---------------------------------------------------------------------------

def test_split_pairs_basic():
    assert _split_pairs("env=prod,team=backend") == {"env": "prod", "team": "backend"}


def test_split_pairs_empty():
    assert _split_pairs("") == {}


def test_split_pairs_ignores_token_without_equals():
    assert _split_pairs("env=prod,badtoken") == {"env": "prod"}


# ---------------------------------------------------------------------------
# load_label_config
# ---------------------------------------------------------------------------

def test_load_defaults_no_section():
    cfg = load_label_config()
    assert cfg.labels == {}
    assert cfg.require == {}
    assert cfg.environment == "default"


def test_load_from_dict():
    cfg = load_label_config(
        {"labels": "env=prod", "require": "team=backend", "environment": "production"}
    )
    assert cfg.labels == {"env": "prod"}
    assert cfg.require == {"team": "backend"}
    assert cfg.environment == "production"


def test_load_from_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_LABELS", "env=staging")
    monkeypatch.setenv("VAULTPULL_LABEL_REQUIRE", "team=ops")
    monkeypatch.setenv("VAULTPULL_ENVIRONMENT", "staging")
    cfg = load_label_config()
    assert cfg.labels == {"env": "staging"}
    assert cfg.require == {"team": "ops"}
    assert cfg.environment == "staging"


def test_dict_overrides_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_LABELS", "env=staging")
    cfg = load_label_config({"labels": "env=prod"})
    assert cfg.labels == {"env": "prod"}


# ---------------------------------------------------------------------------
# apply_labels
# ---------------------------------------------------------------------------

def test_no_require_returns_all():
    cfg = LabelConfig(labels={"env": "prod"}, require={})
    secrets = {"DB_PASS": "s3cr3t", "API_KEY": "abc"}
    assert apply_labels(secrets, cfg) == secrets


def test_require_filters_by_global_label():
    cfg = LabelConfig(labels={"env": "prod"}, require={"env": "prod"})
    secrets = {"DB_PASS": "s3cr3t", "API_KEY": "abc"}
    result = apply_labels(secrets, cfg)
    # All secrets inherit global labels so both should pass
    assert result == secrets


def test_require_excludes_mismatched_global_label():
    cfg = LabelConfig(labels={"env": "staging"}, require={"env": "prod"})
    secrets = {"DB_PASS": "s3cr3t"}
    assert apply_labels(secrets, cfg) == {}


def test_per_secret_label_overrides_global():
    cfg = LabelConfig(labels={"env": "prod"}, require={"env": "prod"})
    secrets = {"DB_PASS": "s3cr3t", "DEV_TOKEN": "xyz"}
    # DEV_TOKEN has a per-secret label that overrides env to staging
    per_secret = {"DEV_TOKEN": {"env": "staging"}}
    result = apply_labels(secrets, cfg, secret_labels=per_secret)
    assert "DB_PASS" in result
    assert "DEV_TOKEN" not in result


def test_require_multiple_labels_all_must_match():
    cfg = LabelConfig(
        labels={"env": "prod", "team": "backend"},
        require={"env": "prod", "team": "backend"},
    )
    secrets = {"DB_PASS": "s3cr3t"}
    assert apply_labels(secrets, cfg) == secrets
