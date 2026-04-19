"""Tests for vaultpull.audit module."""

import json
import os
import tempfile

import pytest

from vaultpull.audit import last_sync, read_log, record_sync


@pytest.fixture()
def log_file(tmp_path):
    return str(tmp_path / "audit.log")


def test_record_sync_creates_file(log_file):
    record_sync("secret/app", ".env", ["DB_URL", "API_KEY"], log_path=log_file)
    assert os.path.exists(log_file)


def test_record_sync_valid_json_line(log_file):
    record_sync("secret/app", ".env", ["DB_URL"], log_path=log_file)
    with open(log_file) as fh:
        entry = json.loads(fh.readline())
    assert entry["vault_path"] == "secret/app"
    assert entry["env_file"] == ".env"
    assert entry["keys_written"] == ["DB_URL"]
    assert entry["keys_skipped"] == []
    assert entry["error"] is None
    assert "timestamp" in entry


def test_record_sync_with_skipped_and_error(log_file):
    record_sync(
        "secret/app",
        ".env",
        ["A"],
        skipped=["B"],
        error="permission denied",
        log_path=log_file,
    )
    entry = read_log(log_file)[0]
    assert entry["keys_skipped"] == ["B"]
    assert entry["error"] == "permission denied"


def test_read_log_multiple_entries(log_file):
    record_sync("secret/a", ".env", ["X"], log_path=log_file)
    record_sync("secret/b", ".env.prod", ["Y"], log_path=log_file)
    entries = read_log(log_file)
    assert len(entries) == 2
    assert entries[0]["vault_path"] == "secret/a"
    assert entries[1]["vault_path"] == "secret/b"


def test_read_log_missing_file(log_file):
    assert read_log(log_file) == []


def test_read_log_skips_lines(log_file):
    with open(log_file, "w") as fh:
        fh.write("not json\n")
        fh.write(json.dumps({"vault_path": "ok", "env_file": ".env",
                             "keys_written": [], "keys_skipped": [],
                             "error": None, "timestamp": "t"}) + "\n")
    entries = read_log(log_file)
    assert len(entries) == 1
    assert entries[0]["vault_path"] == "ok"


def test_last_sync_returns_latest(log_file):
    record_sync("secret/first", ".env", [], log_path=log_file)
    record_sync("secret/last", ".env", [], log_path=log_file)
    entry = last_sync(log_file)
    assert entry["vault_path"] == "secret/last"


def test_last_sync_empty_log(log_file):
    assert last_sync(log_file) is None
