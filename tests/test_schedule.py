"""Tests for vaultpull.schedule."""

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from vaultpull.schedule import (
    ScheduleConfig,
    is_due,
    load_schedule_config,
    next_run,
    read_last_run,
    record_run,
)


# ---------------------------------------------------------------------------
# load_schedule_config
# ---------------------------------------------------------------------------

def test_load_defaults_no_section():
    cfg = load_schedule_config({})
    assert cfg.enabled is False
    assert cfg.interval == "daily"
    assert cfg.jitter_seconds == 0


def test_load_from_dict_full():
    cfg = load_schedule_config({"schedule": {"enabled": "true", "interval": "hourly", "jitter_seconds": "30"}})
    assert cfg.enabled is True
    assert cfg.interval == "hourly"
    assert cfg.jitter_seconds == 30


def test_load_from_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_SCHEDULE_ENABLED", "1")
    monkeypatch.setenv("VAULTPULL_SCHEDULE_INTERVAL", "weekly")
    cfg = load_schedule_config({})
    assert cfg.enabled is True
    assert cfg.interval == "weekly"


def test_dict_overrides_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_SCHEDULE_INTERVAL", "weekly")
    cfg = load_schedule_config({"schedule": {"interval": "hourly"}})
    assert cfg.interval == "hourly"


def test_invalid_interval():
    with pytest.raises(ValueError, match="Invalid schedule interval"):
        load_schedule_config({"schedule": {"interval": "minutely"}})


# ---------------------------------------------------------------------------
# next_run / is_due
# ---------------------------------------------------------------------------

def test_next_run_daily():
    cfg = ScheduleConfig(interval="daily")
    base = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    assert next_run(base, cfg) == datetime(2024, 1, 2, 12, 0, tzinfo=timezone.utc)


def test_next_run_hourly():
    cfg = ScheduleConfig(interval="hourly")
    base = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    assert next_run(base, cfg) == datetime(2024, 1, 1, 13, 0, tzinfo=timezone.utc)


def test_is_due_no_state_file(tmp_path):
    cfg = ScheduleConfig(interval="daily", state_file=str(tmp_path / "state"))
    assert is_due(cfg) is True


def test_is_due_recent(tmp_path):
    state = tmp_path / "state"
    now = datetime.now(tz=timezone.utc)
    state.write_text(now.isoformat())
    cfg = ScheduleConfig(interval="daily", state_file=str(state))
    assert is_due(cfg, now=now) is False


def test_is_due_overdue(tmp_path):
    state = tmp_path / "state"
    past = datetime.now(tz=timezone.utc) - timedelta(days=2)
    state.write_text(past.isoformat())
    cfg = ScheduleConfig(interval="daily", state_file=str(state))
    assert is_due(cfg) is True


# ---------------------------------------------------------------------------
# record_run / read_last_run
# ---------------------------------------------------------------------------

def test_record_and_read(tmp_path):
    state = str(tmp_path / "state")
    when = datetime(2024, 6, 15, 9, 0, tzinfo=timezone.utc)
    record_run(state, when)
    assert read_last_run(state) == when


def test_read_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_last_run(str(tmp_path / "missing"))
