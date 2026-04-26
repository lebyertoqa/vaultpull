"""Tests for vaultpull.secret_checksum."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vaultpull.secret_checksum import (
    ChecksumRecord,
    _checksum,
    build_checksum_report,
    compute_checksums,
    format_checksum_report,
    load_checksums,
    save_checksums,
)


@pytest.fixture()
def chk_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_checksum_is_stable():
    assert _checksum("hello") == _checksum("hello")


def test_checksum_differs_on_value_change():
    assert _checksum("hello") != _checksum("world")


def test_checksum_record_roundtrip():
    rec = ChecksumRecord(key="DB_PASS", digest="abc123")
    restored = ChecksumRecord.from_dict(rec.to_dict())
    assert restored.key == rec.key
    assert restored.digest == rec.digest
    assert restored.algorithm == "sha256"


def test_compute_checksums_keys_match():
    secrets = {"A": "val1", "B": "val2"}
    result = compute_checksums(secrets)
    assert set(result.keys()) == {"A", "B"}
    assert result["A"].digest == _checksum("val1")


def test_save_and_load_checksums(chk_dir):
    records = compute_checksums({"X": "secret"})
    save_checksums(chk_dir, "prod", records)
    loaded = load_checksums(chk_dir, "prod")
    assert "X" in loaded
    assert loaded["X"].digest == records["X"].digest


def test_load_checksums_missing_file(chk_dir):
    result = load_checksums(chk_dir, "nonexistent")
    assert result == {}


def test_load_checksums_corrupt_file(chk_dir):
    path = chk_dir / ".vaultpull_checksums_bad.json"
    path.write_text("NOT JSON")
    result = load_checksums(chk_dir, "bad")
    assert result == {}


def test_build_report_new_keys(chk_dir):
    secrets = {"NEW_KEY": "value"}
    report = build_checksum_report(secrets, chk_dir, environment="dev")
    assert "NEW_KEY" in report.new_keys
    assert report.tampered == []
    assert not report.has_issues


def test_build_report_no_changes(chk_dir):
    secrets = {"STABLE": "same_value"}
    build_checksum_report(secrets, chk_dir, environment="dev")
    report = build_checksum_report(secrets, chk_dir, environment="dev")
    assert report.new_keys == []
    assert report.tampered == []


def test_build_report_detects_tampering(chk_dir):
    secrets_v1 = {"API_KEY": "original"}
    build_checksum_report(secrets_v1, chk_dir, environment="staging")
    secrets_v2 = {"API_KEY": "changed"}
    report = build_checksum_report(secrets_v2, chk_dir, environment="staging")
    assert "API_KEY" in report.tampered
    assert report.has_issues


def test_format_report_ok(chk_dir):
    secrets = {"K": "v"}
    report = build_checksum_report(secrets, chk_dir, environment="test")
    build_checksum_report(secrets, chk_dir, environment="test")
    output = format_checksum_report(report)
    assert "test" in output
    assert "Total keys" in output


def test_format_report_shows_tampered(chk_dir):
    build_checksum_report({"SECRET": "old"}, chk_dir, environment="qa")
    report = build_checksum_report({"SECRET": "new"}, chk_dir, environment="qa")
    output = format_checksum_report(report)
    assert "Tampered" in output
    assert "SECRET" in output
