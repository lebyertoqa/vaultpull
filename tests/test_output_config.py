"""Tests for vaultpull.output_config."""
import pytest

from vaultpull.output_config import OutputConfig, load_output_config
from vaultpull.output_format import OutputFormat


def test_load_defaults_no_section():
    cfg = load_output_config({})
    assert cfg.format == OutputFormat.TEXT
    assert cfg.color is True
    assert cfg.quiet is False


def test_load_from_dict_full():
    cfg = load_output_config({"output": {"format": "json", "color": "false", "quiet": "true"}})
    assert cfg.format == OutputFormat.JSON
    assert cfg.color is False
    assert cfg.quiet is True


def test_load_table_format():
    cfg = load_output_config({"output": {"format": "table"}})
    assert cfg.format == OutputFormat.TABLE


def test_invalid_format_falls_back_to_text():
    cfg = load_output_config({"output": {"format": "xml"}})
    assert cfg.format == OutputFormat.TEXT


def test_load_format_from_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_OUTPUT_FORMAT", "json")
    cfg = load_output_config({})
    assert cfg.format == OutputFormat.JSON


def test_dict_takes_precedence_over_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_OUTPUT_FORMAT", "table")
    cfg = load_output_config({"output": {"format": "json"}})
    assert cfg.format == OutputFormat.JSON


def test_color_from_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_OUTPUT_COLOR", "0")
    cfg = load_output_config({})
    assert cfg.color is False


def test_quiet_from_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_OUTPUT_QUIET", "true")
    cfg = load_output_config({})
    assert cfg.quiet is True


def test_none_cfg_uses_defaults():
    cfg = load_output_config(None)
    assert cfg.format == OutputFormat.TEXT
    assert cfg.color is True
    assert cfg.quiet is False
