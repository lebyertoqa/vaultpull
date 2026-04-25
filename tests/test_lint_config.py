"""Tests for vaultpull.lint_config and lint_config_loader."""
import pytest
from vaultpull.lint_config import load_lint_config, LintConfig
from vaultpull.lint_config_loader import get_lint_config, describe_lint


def test_load_defaults_no_section():
    cfg = load_lint_config({})
    assert cfg.enabled is True
    assert cfg.fail_on_error is False
    assert cfg.skip_keys == []
    assert cfg.skip_convention_check is False
    assert cfg.skip_weak_check is False


def test_load_from_dict():
    cfg = load_lint_config({"lint": {
        "enabled": "false",
        "fail_on_error": "true",
        "skip_keys": "SECRET,TOKEN",
    }})
    assert cfg.enabled is False
    assert cfg.fail_on_error is True
    assert cfg.skip_keys == ["SECRET", "TOKEN"]


def test_load_from_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_LINT_ENABLED", "false")
    monkeypatch.setenv("VAULTPULL_LINT_FAIL_ON_ERROR", "true")
    monkeypatch.setenv("VAULTPULL_LINT_SKIP_KEYS", "FOO,BAR")
    cfg = load_lint_config({})
    assert cfg.enabled is False
    assert cfg.fail_on_error is True
    assert "FOO" in cfg.skip_keys
    assert "BAR" in cfg.skip_keys


def test_dict_takes_precedence_over_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_LINT_ENABLED", "false")
    cfg = load_lint_config({"lint": {"enabled": "true"}})
    assert cfg.enabled is True


def test_skip_convention_from_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_LINT_SKIP_CONVENTION", "1")
    cfg = load_lint_config({})
    assert cfg.skip_convention_check is True


def test_skip_weak_from_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_LINT_SKIP_WEAK", "true")
    cfg = load_lint_config({})
    assert cfg.skip_weak_check is True


def test_get_lint_config_wrapper():
    cfg = get_lint_config({"lint": {"fail_on_error": "true"}})
    assert isinstance(cfg, LintConfig)
    assert cfg.fail_on_error is True


def test_describe_lint_disabled():
    cfg = LintConfig(enabled=False)
    assert describe_lint(cfg) == "Linting: disabled"


def test_describe_lint_enabled_defaults():
    cfg = LintConfig(enabled=True)
    result = describe_lint(cfg)
    assert "enabled" in result


def test_describe_lint_full():
    cfg = LintConfig(enabled=True, fail_on_error=True,
                     skip_keys=["A", "B"], skip_convention_check=True)
    result = describe_lint(cfg)
    assert "fail-on-error" in result
    assert "A,B" in result
    assert "skip-convention" in result
