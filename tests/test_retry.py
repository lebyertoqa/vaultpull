"""Tests for vaultpull.retry."""

import pytest
from unittest.mock import patch, call
from vaultpull.retry import RetryConfig, load_retry_config, with_retry


def test_load_defaults_no_section():
    cfg = load_retry_config()
    assert cfg.max_attempts == 3
    assert cfg.backoff_base == 1.0
    assert cfg.backoff_max == 30.0


def test_load_from_dict():
    cfg = load_retry_config({"max_attempts": "5", "backoff_base": "0.5", "backoff_max": "10"})
    assert cfg.max_attempts == 5
    assert cfg.backoff_base == 0.5
    assert cfg.backoff_max == 10.0


def test_with_retry_success_first_try():
    calls = []
    def fn():
        calls.append(1)
        return "ok"
    cfg = RetryConfig(max_attempts=3, backoff_base=0.0)
    result = with_retry(fn, cfg)
    assert result == "ok"
    assert len(calls) == 1


def test_with_retry_succeeds_on_second_attempt():
    attempts = []
    def fn():
        attempts.append(1)
        if len(attempts) < 2:
            raise ValueError("fail")
        return "ok"
    cfg = RetryConfig(max_attempts=3, backoff_base=0.0, retryable_exceptions=(ValueError,))
    with patch("vaultpull.retry.time.sleep") as mock_sleep:
        result = with_retry(fn, cfg)
    assert result == "ok"
    assert len(attempts) == 2
    mock_sleep.assert_called_once_with(0.0)


def test_with_retry_exhausts_all_attempts():
    def fn():
        raise ConnectionError("down")
    cfg = RetryConfig(max_attempts=3, backoff_base=0.0, retryable_exceptions=(ConnectionError,))
    with patch("vaultpull.retry.time.sleep"):
        with pytest.raises(ConnectionError, match="down"):
            with_retry(fn, cfg)


def test_with_retry_non_retryable_raises_immediately():
    calls = []
    def fn():
        calls.append(1)
        raise TypeError("bad type")
    cfg = RetryConfig(max_attempts=3, backoff_base=0.0, retryable_exceptions=(ValueError,))
    with pytest.raises(TypeError):
        with_retry(fn, cfg)
    assert len(calls) == 1


def test_backoff_capped_at_max():
    sleeps = []
    def fn():
        raise OSError("err")
    cfg = RetryConfig(max_attempts=4, backoff_base=10.0, backoff_max=15.0, retryable_exceptions=(OSError,))
    with patch("vaultpull.retry.time.sleep", side_effect=lambda d: sleeps.append(d)):
        with pytest.raises(OSError):
            with_retry(fn, cfg)
    assert all(d <= 15.0 for d in sleeps)
    assert sleeps[1] == 15.0
