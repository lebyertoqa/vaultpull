"""Tests for vaultpull.redact."""

import pytest
from vaultpull.redact import (
    should_redact,
    redact_value,
    redact_dict,
    redact_message,
    _PLACEHOLDER,
)


# ---------------------------------------------------------------------------
# should_redact
# ---------------------------------------------------------------------------

def test_should_redact_password():
    assert should_redact("DB_PASSWORD") is True


def test_should_redact_token():
    assert should_redact("GITHUB_TOKEN") is True


def test_should_redact_api_key():
    assert should_redact("STRIPE_API_KEY") is True


def test_should_redact_plain_key_false():
    assert should_redact("DATABASE_HOST") is False


def test_should_redact_case_insensitive():
    assert should_redact("db_secret") is True


# ---------------------------------------------------------------------------
# redact_value
# ---------------------------------------------------------------------------

def test_redact_value_sensitive_returns_placeholder():
    assert redact_value("API_KEY", "supersecret123") == _PLACEHOLDER


def test_redact_value_non_sensitive_unchanged():
    assert redact_value("APP_PORT", "8080") == "8080"


def test_redact_value_partial_shows_prefix():
    result = redact_value("DB_PASSWORD", "supersecret123", partial=True)
    assert result.startswith("supe")
    assert "*" in result
    assert "supersecret123" not in result


def test_redact_value_partial_short_value_uses_placeholder():
    # Value too short to partially reveal
    result = redact_value("DB_PASSWORD", "abc", partial=True)
    assert result == _PLACEHOLDER


# ---------------------------------------------------------------------------
# redact_dict
# ---------------------------------------------------------------------------

def test_redact_dict_redacts_sensitive_keys():
    secrets = {"DB_PASSWORD": "hunter2", "APP_HOST": "localhost"}
    result = redact_dict(secrets)
    assert result["DB_PASSWORD"] == _PLACEHOLDER
    assert result["APP_HOST"] == "localhost"


def test_redact_dict_safe_keys_bypass_redaction():
    secrets = {"DB_PASSWORD": "hunter2"}
    result = redact_dict(secrets, safe_keys={"DB_PASSWORD"})
    assert result["DB_PASSWORD"] == "hunter2"


def test_redact_dict_does_not_mutate_original():
    secrets = {"TOKEN": "abc123"}
    redact_dict(secrets)
    assert secrets["TOKEN"] == "abc123"


# ---------------------------------------------------------------------------
# redact_message
# ---------------------------------------------------------------------------

def test_redact_message_replaces_secret_in_text():
    secrets = {"DB_PASSWORD": "hunter2"}
    msg = "Connection failed: hunter2 is wrong"
    result = redact_message(msg, secrets)
    assert "hunter2" not in result
    assert _PLACEHOLDER in result


def test_redact_message_ignores_non_sensitive_values():
    secrets = {"APP_HOST": "localhost"}
    msg = "Connecting to localhost"
    result = redact_message(msg, secrets)
    assert result == msg


def test_redact_message_empty_value_skipped():
    secrets = {"DB_PASSWORD": ""}
    msg = "some log line"
    assert redact_message(msg, secrets) == msg
