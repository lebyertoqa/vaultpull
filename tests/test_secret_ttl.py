"""Tests for vaultpull.secret_ttl."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from vaultpull.secret_ttl import (
    TtlRecord,
    load_ttl_records,
    save_ttl_records,
    record_ttl,
    expired_keys,
)


@pytest.fixture
def ttl_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_ttl_record_not_expired():
    rec = TtlRecord(key="FOO", fetched_at=time.time(), ttl_seconds=3600)
    assert not rec.is_expired
    assert rec.seconds_remaining > 3590


def test_ttl_record_expired():
    rec = TtlRecord(key="FOO", fetched_at=time.time() - 7200, ttl_seconds=3600)
    assert rec.is_expired
    assert rec.seconds_remaining == 0.0


def test_ttl_record_roundtrip():
    rec = TtlRecord(key="BAR", fetched_at=1_700_000_000.0, ttl_seconds=600)
    restored = TtlRecord.from_dict(rec.to_dict())
    assert restored.key == rec.key
    assert restored.fetched_at == rec.fetched_at
    assert restored.ttl_seconds == rec.ttl_seconds


def test_load_ttl_records_missing_file(ttl_dir: Path):
    assert load_ttl_records(ttl_dir) == {}


def test_load_ttl_records_corrupt_file(ttl_dir: Path):
    (ttl_dir / ".vaultpull_ttl.json").write_text("not json!!!")
    assert load_ttl_records(ttl_dir) == {}


def test_save_and_load_ttl_records(ttl_dir: Path):
    records = {
        "DB_PASS": TtlRecord(key="DB_PASS", fetched_at=1_700_000_000.0, ttl_seconds=300),
        "API_KEY": TtlRecord(key="API_KEY", fetched_at=1_700_000_500.0, ttl_seconds=900),
    }
    save_ttl_records(ttl_dir, records)
    loaded = load_ttl_records(ttl_dir)
    assert set(loaded.keys()) == {"DB_PASS", "API_KEY"}
    assert loaded["DB_PASS"].ttl_seconds == 300
    assert loaded["API_KEY"].fetched_at == 1_700_000_500.0


def test_record_ttl_creates_records(ttl_dir: Path):
    secrets = {"SECRET_A": "val1", "SECRET_B": "val2"}
    records = record_ttl(ttl_dir, secrets, ttl_seconds=120)
    assert "SECRET_A" in records
    assert "SECRET_B" in records
    assert records["SECRET_A"].ttl_seconds == 120
    assert not records["SECRET_A"].is_expired


def test_record_ttl_persists_to_disk(ttl_dir: Path):
    record_ttl(ttl_dir, {"MY_KEY": "myval"}, ttl_seconds=60)
    loaded = load_ttl_records(ttl_dir)
    assert "MY_KEY" in loaded


def test_record_ttl_refreshes_existing(ttl_dir: Path):
    old = {"OLD_KEY": TtlRecord(key="OLD_KEY", fetched_at=time.time() - 9999, ttl_seconds=100)}
    save_ttl_records(ttl_dir, old)
    record_ttl(ttl_dir, {"OLD_KEY": "refreshed"}, ttl_seconds=500)
    loaded = load_ttl_records(ttl_dir)
    assert loaded["OLD_KEY"].ttl_seconds == 500
    assert not loaded["OLD_KEY"].is_expired


def test_expired_keys_returns_stale(ttl_dir: Path):
    records = {
        "FRESH": TtlRecord(key="FRESH", fetched_at=time.time(), ttl_seconds=3600),
        "STALE": TtlRecord(key="STALE", fetched_at=time.time() - 7200, ttl_seconds=3600),
    }
    save_ttl_records(ttl_dir, records)
    expired = expired_keys(ttl_dir)
    assert "STALE" in expired
    assert "FRESH" not in expired


def test_expired_keys_empty_dir(ttl_dir: Path):
    assert expired_keys(ttl_dir) == []
