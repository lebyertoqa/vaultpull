"""Tests for secret_access_log and access_log_report."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vaultpull.secret_access_log import (
    AccessRecord,
    record_access,
    load_access_log,
)
from vaultpull.access_log_report import build_access_log_report, format_access_log_report


@pytest.fixture()
def log_dir(tmp_path: Path) -> Path:
    return tmp_path


SECRETS = {"DB_PASSWORD": "s3cr3t", "API_KEY": "abc123"}


def test_record_access_returns_log(log_dir):
    log = record_access(SECRETS, "secret/myapp", "staging", base_dir=log_dir)
    assert log.total == 2
    assert log.environment == "staging"


def test_record_access_creates_file(log_dir):
    record_access(SECRETS, "secret/myapp", "staging", base_dir=log_dir)
    log_file = log_dir / ".vaultpull_access_staging.jsonl"
    assert log_file.exists()


def test_record_access_valid_jsonl(log_dir):
    record_access(SECRETS, "secret/myapp", "staging", base_dir=log_dir)
    log_file = log_dir / ".vaultpull_access_staging.jsonl"
    lines = [l for l in log_file.read_text().splitlines() if l.strip()]
    assert len(lines) == 2
    for line in lines:
        data = json.loads(line)
        assert "key" in data
        assert "accessed_at" in data
        assert data["environment"] == "staging"


def test_record_access_cached_flag(log_dir):
    log = record_access(SECRETS, "secret/myapp", "prod", base_dir=log_dir, was_cached=True)
    assert log.cached_count == 2
    assert log.total - log.cached_count == 0


def test_load_access_log_missing_file(log_dir):
    records = load_access_log("nonexistent", base_dir=log_dir)
    assert records == []


def test_load_access_log_roundtrip(log_dir):
    record_access(SECRETS, "secret/myapp", "dev", base_dir=log_dir)
    records = load_access_log("dev", base_dir=log_dir)
    assert len(records) == 2
    keys = {r.key for r in records}
    assert keys == set(SECRETS.keys())


def test_load_access_log_limit(log_dir):
    for _ in range(5):
        record_access(SECRETS, "secret/myapp", "dev", base_dir=log_dir)
    records = load_access_log("dev", base_dir=log_dir, limit=3)
    assert len(records) == 3


def test_access_record_from_dict_roundtrip():
    original = AccessRecord(
        key="TOKEN", path="secret/app", accessed_at="2024-01-01T00:00:00+00:00",
        environment="prod", was_cached=False,
    )
    assert AccessRecord.from_dict(original.to_dict()) == original


def test_build_access_log_report(log_dir):
    log = record_access(SECRETS, "secret/myapp", "staging", base_dir=log_dir)
    report = build_access_log_report(log)
    assert report.total == 2
    assert report.live == 2
    assert report.cached == 0
    assert "secret/myapp" in report.by_path


def test_format_access_log_report_contains_env(log_dir):
    log = record_access(SECRETS, "secret/myapp", "staging", base_dir=log_dir)
    report = build_access_log_report(log)
    text = format_access_log_report(report)
    assert "staging" in text
    assert "secret/myapp" in text
    assert "Total keys accessed" in text
