"""Tests for vaultpull.mask."""

import pytest
from vaultpull.mask import is_sensitive, mask_value, mask_secrets, DEFAULT_MASK


# --- is_sensitive ---

def test_is_sensitive_password():
    assert is_sensitive("DB_PASSWORD") is True

def test_is_sensitive_token():
    assert is_sensitive("GITHUB_TOKEN") is True

def test_is_sensitive_api_key():
    assert is_sensitive("STRIPE_API_KEY") is True

def test_is_sensitive_plain_key():
    assert is_sensitive("APP_ENV") is False

def test_is_sensitive_case_insensitive():
    assert is_sensitive("db_Secret") is True


# --- mask_value ---

def test_mask_value_basic():
    assert mask_value("supersecret") == DEFAULT_MASK

def test_mask_value_empty():
    assert mask_value("") == DEFAULT_MASK

def test_mask_value_visible_chars():
    result = mask_value("supersecret", visible_chars=3)
    assert result == DEFAULT_MASK + "ret"

def test_mask_value_visible_chars_short_value():
    # value shorter than visible_chars — just mask fully
    result = mask_value("ab", visible_chars=5)
    assert result == DEFAULT_MASK


# --- mask_secrets ---

def test_mask_secrets_masks_sensitive():
    secrets = {"DB_PASSWORD": "hunter2", "APP_ENV": "production"}
    result = mask_secrets(secrets)
    assert result["DB_PASSWORD"] == DEFAULT_MASK
    assert result["APP_ENV"] == "production"

def test_mask_secrets_force_mask_all():
    secrets = {"APP_ENV": "production", "PORT": "5432"}
    result = mask_secrets(secrets, force_mask_all=True)
    assert all(v == DEFAULT_MASK for v in result.values())

def test_mask_secrets_does_not_mutate_original():
    secrets = {"DB_PASSWORD": "hunter2"}
    mask_secrets(secrets)
    assert secrets["DB_PASSWORD"] == "hunter2"

def test_mask_secrets_visible_chars_propagated():
    secrets = {"API_TOKEN": "abcdef"}
    result = mask_secrets(secrets, visible_chars=2)
    assert result["API_TOKEN"] == DEFAULT_MASK + "ef"

def test_mask_secrets_empty_dict():
    assert mask_secrets({}) == {}
