"""Simple schedule config and next-run calculation for vaultpull."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional


VALID_INTERVALS = ("hourly", "daily", "weekly")

INTERVAL_DELTA: dict[str, timedelta] = {
    "hourly": timedelta(hours=1),
    "daily": timedelta(days=1),
    "weekly": timedelta(weeks=1),
}


@dataclass
class ScheduleConfig:
    enabled: bool = False
    interval: str = "daily"  # hourly | daily | weekly
    jitter_seconds: int = 0
    state_file: str = ".vaultpull_schedule"


def load_schedule_config(cfg: Optional[dict] = None) -> ScheduleConfig:
    """Build ScheduleConfig from optional config dict, falling back to env vars."""
    cfg = cfg or {}
    section = cfg.get("schedule", {})

    def _bool(val: str) -> bool:
        return val.lower() in ("1", "true", "yes")

    enabled = _bool(str(section.get("enabled", os.environ.get("VAULTPULL_SCHEDULE_ENABLED", "false"))))
    interval = section.get("interval", os.environ.get("VAULTPULL_SCHEDULE_INTERVAL", "daily"))
    jitter = int(section.get("jitter_seconds", os.environ.get("VAULTPULL_SCHEDULE_JITTER", "0")))
    state_file = section.get("state_file", os.environ.get("VAULTPULL_SCHEDULE_STATE_FILE", ".vaultpull_schedule"))

    if interval not in VALID_INTERVALS:
        raise ValueError(f"Invalid schedule interval '{interval}'. Choose from {VALID_INTERVALS}.")

    return ScheduleConfig(enabled=enabled, interval=interval, jitter_seconds=jitter, state_file=state_file)


def next_run(last: datetime, config: ScheduleConfig) -> datetime:
    """Return the datetime when the next sync should occur."""
    delta = INTERVAL_DELTA[config.interval]
    return last + delta


def is_due(config: ScheduleConfig, now: Optional[datetime] = None) -> bool:
    """Return True if a sync is due based on the state file."""
    now = now or datetime.now(tz=timezone.utc)
    try:
        last = read_last_run(config.state_file)
    except FileNotFoundError:
        return True
    return now >= next_run(last, config)


def record_run(state_file: str, when: Optional[datetime] = None) -> None:
    """Write the current UTC time to the state file."""
    when = when or datetime.now(tz=timezone.utc)
    with open(state_file, "w") as fh:
        fh.write(when.isoformat())


def read_last_run(state_file: str) -> datetime:
    """Read the last run datetime from the state file."""
    with open(state_file) as fh:
        return datetime.fromisoformat(fh.read().strip())
