"""Tests for vaultpull.notify."""

import json
from unittest.mock import MagicMock, patch

import pytest

from vaultpull.notify import NotifyConfig, _build_payload, notify_sync, send_webhook


WEBHOOK = "http://example.com/hook"


def test_build_payload_basic():
    p = _build_payload("success", ".env", 2, 1, 0)
    assert p["status"] == "success"
    assert p["env_file"] == ".env"
    assert p["changes"] == {"added": 2, "changed": 1, "removed": 0}
    assert "error" not in p


def test_build_payload_with_error():
    p = _build_payload("failure", ".env", 0, 0, 0, error="timeout")
    assert p["error"] == "timeout"


def test_send_webhook_success():
    cfg = NotifyConfig(webhook_url=WEBHOOK)
    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = send_webhook(cfg, {"status": "success"})
    assert result is True


def test_send_webhook_no_url():
    cfg = NotifyConfig(webhook_url=None)
    assert send_webhook(cfg, {}) is False


def test_send_webhook_url_error():
    import urllib.error
    cfg = NotifyConfig(webhook_url=WEBHOOK)
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("fail")):
        result = send_webhook(cfg, {"status": "failure"})
    assert result is False


def test_notify_sync_success_enabled():
    cfg = NotifyConfig(webhook_url=WEBHOOK, on_success=True)
    with patch("vaultpull.notify.send_webhook", return_value=True) as mock_send:
        result = notify_sync(cfg, "success", ".env", added=3)
    assert result is True
    mock_send.assert_called_once()


def test_notify_sync_success_disabled():
    cfg = NotifyConfig(webhook_url=WEBHOOK, on_success=False)
    with patch("vaultpull.notify.send_webhook") as mock_send:
        result = notify_sync(cfg, "success", ".env")
    assert result is False
    mock_send.assert_not_called()


def test_notify_sync_no_changes_disabled_by_default():
    cfg = NotifyConfig(webhook_url=WEBHOOK)
    with patch("vaultpull.notify.send_webhook") as mock_send:
        result = notify_sync(cfg, "no_changes", ".env")
    assert result is False
    mock_send.assert_not_called()


def test_notify_sync_failure_enabled():
    cfg = NotifyConfig(webhook_url=WEBHOOK, on_failure=True)
    with patch("vaultpull.notify.send_webhook", return_value=True) as mock_send:
        result = notify_sync(cfg, "failure", ".env", error="vault down")
    assert result is True


def test_notify_sync_no_webhook():
    cfg = NotifyConfig(webhook_url=None)
    result = notify_sync(cfg, "success", ".env")
    assert result is False
