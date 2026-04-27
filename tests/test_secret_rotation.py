"""Tests for vaultpull.secret_rotation."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from vaultpull.secret_rotation import (
    RotationRecord,
    get_stale_secrets,
    load_rotation_records,
    mark_rotated,
    save_rotation_records,
)


@pytest.fixture
def rot_dir(tmp_path: Path) -> Path:
    return tmp_path


# --- RotationRecord unit tests ---

def test_rotation_record_not_stale():
    now = datetime.now(timezone.utc)
    rec = RotationRecord(key="DB_PASS", last_rotated=now.isoformat(), rotation_interval_days=90)
    assert not rec.is_stale()
    assert rec.days_until_due() > 0


def test_rotation_record_stale():
    old = datetime.now(timezone.utc) - timedelta(days=100)
    rec = RotationRecord(key="DB_PASS", last_rotated=old.isoformat(), rotation_interval_days=90)
    assert rec.is_stale()
    assert rec.days_until_due() < 0


def test_rotation_record_roundtrip():
    now = datetime.now(timezone.utc).isoformat()
    rec = RotationRecord(key="API_KEY", last_rotated=now, rotation_interval_days=30, environment="prod")
    restored = RotationRecord.from_dict(rec.to_dict())
    assert restored.key == rec.key
    assert restored.last_rotated == rec.last_rotated
    assert restored.rotation_interval_days == rec.rotation_interval_days
    assert restored.environment == rec.environment


# --- Persistence tests ---

def test_load_rotation_records_missing_file(rot_dir):
    result = load_rotation_records(rot_dir, environment="staging")
    assert result == {}


def test_save_and_load_rotation_records(rot_dir):
    now = datetime.now(timezone.utc).isoformat()
    records = {
        "SECRET_A": RotationRecord("SECRET_A", now, 60, "dev"),
        "SECRET_B": RotationRecord("SECRET_B", now, 30, "dev"),
    }
    save_rotation_records(records, rot_dir, environment="dev")
    loaded = load_rotation_records(rot_dir, environment="dev")
    assert set(loaded.keys()) == {"SECRET_A", "SECRET_B"}
    assert loaded["SECRET_A"].rotation_interval_days == 60


def test_load_rotation_records_corrupt_file(rot_dir):
    path = rot_dir / ".vaultpull_rotation_default.json"
    path.write_text("not valid json{{{")
    result = load_rotation_records(rot_dir)
    assert result == {}


# --- mark_rotated tests ---

def test_mark_rotated_creates_record(rot_dir):
    rec = mark_rotated("MY_SECRET", rot_dir, interval_days=45)
    assert rec.key == "MY_SECRET"
    assert rec.rotation_interval_days == 45
    assert not rec.is_stale()


def test_mark_rotated_persists(rot_dir):
    mark_rotated("PERSISTED", rot_dir, interval_days=60)
    loaded = load_rotation_records(rot_dir)
    assert "PERSISTED" in loaded


# --- get_stale_secrets tests ---

def test_get_stale_secrets_no_records_returns_all(rot_dir):
    secrets = {"KEY_A": "val1", "KEY_B": "val2"}
    stale = get_stale_secrets(secrets, rot_dir, interval_days=90)
    assert {r.key for r in stale} == {"KEY_A", "KEY_B"}


def test_get_stale_secrets_fresh_not_included(rot_dir):
    mark_rotated("FRESH_KEY", rot_dir, interval_days=90)
    secrets = {"FRESH_KEY": "value"}
    stale = get_stale_secrets(secrets, rot_dir, interval_days=90)
    assert stale == []


def test_get_stale_secrets_mixed(rot_dir):
    mark_rotated("FRESH", rot_dir, interval_days=90)
    secrets = {"FRESH": "v1", "OLD": "v2"}
    stale = get_stale_secrets(secrets, rot_dir, interval_days=90)
    assert len(stale) == 1
    assert stale[0].key == "OLD"
