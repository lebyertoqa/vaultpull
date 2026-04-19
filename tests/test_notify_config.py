"""Tests for vaultpull.notify_config."""

import pytest
from unittest.mock import patch

from vaultpull.notify_config import load_notify_config


def test_load_from_dict_full():
    raw = {
        "notify": {
            "webhook_url": "http://hook.example.com",
            "on_success": False,
            "on_failure": True,
            "on_no_changes": True,
        }
    }
    cfg = load_notify_config(raw)
    assert cfg.webhook_url == "http://hook.example.com"
    assert cfg.on_success is False
    assert cfg.on_failure is True
    assert cfg.on_no_changes is True


def test_load_defaults_no_section():
    cfg = load_notify_config({})
    assert cfg.webhook_url is None
    assert cfg.on_success is True
    assert cfg.on_failure is True
    assert cfg.on_no_changes is False


def test_load_webhook_from_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_WEBHOOK_URL", "http://env-hook.example.com")
    cfg = load_notify_config({})
    assert cfg.webhook_url == "http://env-hook.example.com"


def test_dict_takes_precedence_over_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_WEBHOOK_URL", "http://env-hook.example.com")
    raw = {"notify": {"webhook_url": "http://dict-hook.example.com"}}
    cfg = load_notify_config(raw)
    assert cfg.webhook_url == "http://dict-hook.example.com"


def test_bool_flags_from_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_NOTIFY_SUCCESS", "false")
    monkeypatch.setenv("VAULTPULL_NOTIFY_NO_CHANGES", "1")
    cfg = load_notify_config({})
    assert cfg.on_success is False
    assert cfg.on_no_changes is True


def test_empty_webhook_url_becomes_none():
    raw = {"notify": {"webhook_url": ""}}
    cfg = load_notify_config(raw)
    assert cfg.webhook_url is None
