"""Tests for vaultpull.validate."""
import pytest
from vaultpull.validate import (
    ValidationRule,
    load_validation_config,
    validate_secrets,
)


def test_load_defaults_no_section():
    rule = load_validation_config({})
    assert rule.min_length == 0
    assert rule.max_length == 65536
    assert rule.required_keys == []
    assert rule.forbidden_keys == []
    assert rule.key_pattern is None


def test_load_from_dict():
    cfg = {"validate": {"min_length": "4", "max_length": "128", "key_pattern": "^[A-Z_]+$"}}
    rule = load_validation_config(cfg)
    assert rule.min_length == 4
    assert rule.max_length == 128
    assert rule.key_pattern == "^[A-Z_]+$"


def test_load_required_and_forbidden():
    cfg = {"validate": {"required_keys": "DB_URL, API_KEY", "forbidden_keys": "DEBUG"}}
    rule = load_validation_config(cfg)
    assert rule.required_keys == ["DB_URL", "API_KEY"]
    assert rule.forbidden_keys == ["DEBUG"]


def test_validate_passes_empty_rule():
    result = validate_secrets({"FOO": "bar", "BAZ": "qux"}, ValidationRule())
    assert result.valid
    assert result.errors == []


def test_validate_required_key_missing():
    rule = ValidationRule(required_keys=["MUST_EXIST"])
    result = validate_secrets({"OTHER": "val"}, rule)
    assert not result.valid
    assert any("MUST_EXIST" in e for e in result.errors)


def test_validate_forbidden_key_present():
    rule = ValidationRule(forbidden_keys=["SECRET"])
    result = validate_secrets({"SECRET": "oops"}, rule)
    assert not result.valid
    assert any("SECRET" in e for e in result.errors)


def test_validate_key_pattern_mismatch():
    rule = ValidationRule(key_pattern="^[A-Z_]+$")
    result = validate_secrets({"valid_KEY": "x", "lowercase": "y"}, rule)
    assert not result.valid
    assert len([e for e in result.errors if "does not match" in e]) == 2


def test_validate_min_length():
    rule = ValidationRule(min_length=5)
    result = validate_secrets({"KEY": "ab"}, rule)
    assert not result.valid
    assert any("too short" in e for e in result.errors)


def test_validate_max_length():
    rule = ValidationRule(max_length=3)
    result = validate_secrets({"KEY": "toolong"}, rule)
    assert not result.valid
    assert any("too long" in e for e in result.errors)


def test_validate_multiple_errors():
    rule = ValidationRule(required_keys=["A"], forbidden_keys=["B"], min_length=10)
    result = validate_secrets({"B": "x"}, rule)
    assert not result.valid
    assert len(result.errors) >= 3
