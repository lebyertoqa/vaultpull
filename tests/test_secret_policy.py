"""Tests for vaultpull.secret_policy."""
import pytest
from vaultpull.secret_policy import (
    PolicyConfig,
    PolicyViolation,
    load_policy_config,
    enforce_policy,
)


# ---------------------------------------------------------------------------
# load_policy_config
# ---------------------------------------------------------------------------

def test_load_defaults_no_section():
    cfg = load_policy_config()
    assert cfg.allowed_keys == []
    assert cfg.denied_keys == []
    assert cfg.max_value_length == 0
    assert cfg.require_non_empty is True
    assert cfg.environment == "default"


def test_load_from_dict():
    cfg = load_policy_config({
        "allowed_keys": "DB_*, API_*",
        "denied_keys": "SECRET_OLD",
        "max_value_length": "128",
        "require_non_empty": "false",
        "environment": "staging",
    })
    assert cfg.allowed_keys == ["DB_*", "API_*"]
    assert cfg.denied_keys == ["SECRET_OLD"]
    assert cfg.max_value_length == 128
    assert cfg.require_non_empty is False
    assert cfg.environment == "staging"


def test_load_from_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_POLICY_ALLOWED_KEYS", "TOKEN_*")
    monkeypatch.setenv("VAULTPULL_POLICY_DENIED_KEYS", "OLD_KEY")
    monkeypatch.setenv("VAULTPULL_POLICY_MAX_VALUE_LENGTH", "64")
    monkeypatch.setenv("VAULTPULL_POLICY_REQUIRE_NON_EMPTY", "false")
    monkeypatch.setenv("VAULTPULL_ENVIRONMENT", "production")
    cfg = load_policy_config()
    assert cfg.allowed_keys == ["TOKEN_*"]
    assert cfg.denied_keys == ["OLD_KEY"]
    assert cfg.max_value_length == 64
    assert cfg.require_non_empty is False
    assert cfg.environment == "production"


def test_dict_takes_precedence_over_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_POLICY_ALLOWED_KEYS", "ENV_*")
    cfg = load_policy_config({"allowed_keys": "DICT_*"})
    assert cfg.allowed_keys == ["DICT_*"]


def test_invalid_max_length_falls_back_to_zero():
    cfg = load_policy_config({"max_value_length": "not_a_number"})
    assert cfg.max_value_length == 0


# ---------------------------------------------------------------------------
# enforce_policy
# ---------------------------------------------------------------------------

def test_no_violations_for_clean_secrets():
    cfg = PolicyConfig()
    report = enforce_policy({"DB_HOST": "localhost", "API_KEY": "abc123"}, cfg)
    assert not report.has_violations
    assert report.checked == 2


def test_allowed_keys_blocks_unlisted_key():
    cfg = PolicyConfig(allowed_keys=["DB_*"])
    report = enforce_policy({"DB_HOST": "localhost", "ROGUE_KEY": "value"}, cfg)
    keys_violated = [v.key for v in report.violations]
    assert "ROGUE_KEY" in keys_violated
    assert "DB_HOST" not in keys_violated


def test_denied_keys_blocks_matching_key():
    cfg = PolicyConfig(denied_keys=["OLD_*"])
    report = enforce_policy({"OLD_TOKEN": "abc", "NEW_TOKEN": "xyz"}, cfg)
    keys_violated = [v.key for v in report.violations]
    assert "OLD_TOKEN" in keys_violated
    assert "NEW_TOKEN" not in keys_violated


def test_require_non_empty_flags_empty_value():
    cfg = PolicyConfig(require_non_empty=True)
    report = enforce_policy({"EMPTY_KEY": ""}, cfg)
    assert report.has_violations
    assert report.violations[0].key == "EMPTY_KEY"
    assert "empty" in report.violations[0].reason


def test_require_non_empty_false_allows_empty_value():
    cfg = PolicyConfig(require_non_empty=False)
    report = enforce_policy({"EMPTY_KEY": ""}, cfg)
    assert not report.has_violations


def test_max_value_length_violation():
    cfg = PolicyConfig(max_value_length=5)
    report = enforce_policy({"KEY": "toolongvalue"}, cfg)
    assert report.has_violations
    assert "max length" in report.violations[0].reason


def test_max_value_length_zero_means_unlimited():
    cfg = PolicyConfig(max_value_length=0)
    report = enforce_policy({"KEY": "x" * 10000}, cfg)
    assert not report.has_violations


def test_environment_label_propagated():
    cfg = PolicyConfig(environment="production")
    report = enforce_policy({}, cfg)
    assert report.environment == "production"
