"""Tests for vaultpull.snapshot_report."""
import pytest
from pathlib import Path

from vaultpull.secret_snapshot import capture_snapshot
from vaultpull.snapshot_report import (
    build_snapshot_report,
    format_snapshot_report,
)


SECRETS_V1 = {"DB_PASS": "s3cr3t", "API_KEY": "key1"}
SECRETS_V2 = {"DB_PASS": "s3cr3t", "API_KEY": "key1", "NEW_KEY": "val"}
SECRETS_V3 = {"API_KEY": "key1"}  # DB_PASS removed


@pytest.fixture
def snap_dir(tmp_path: Path) -> Path:
    return tmp_path / "snaps"


def test_build_report_no_previous(snap_dir):
    current = capture_snapshot(SECRETS_V1, "prod", snap_dir)
    report = build_snapshot_report(None, current)
    assert report.changed is True
    assert set(report.added_keys) == set(SECRETS_V1.keys())
    assert report.removed_keys == []


def test_build_report_no_change(snap_dir):
    prev = capture_snapshot(SECRETS_V1, "prev", snap_dir)
    curr = capture_snapshot(SECRETS_V1, "curr", snap_dir)
    report = build_snapshot_report(prev, curr)
    assert report.changed is False
    assert report.added_keys == []
    assert report.removed_keys == []


def test_build_report_added_key(snap_dir):
    prev = capture_snapshot(SECRETS_V1, "prev", snap_dir)
    curr = capture_snapshot(SECRETS_V2, "curr", snap_dir)
    report = build_snapshot_report(prev, curr)
    assert report.changed is True
    assert "NEW_KEY" in report.added_keys
    assert report.removed_keys == []


def test_build_report_removed_key(snap_dir):
    prev = capture_snapshot(SECRETS_V1, "prev", snap_dir)
    curr = capture_snapshot(SECRETS_V3, "curr", snap_dir)
    report = build_snapshot_report(prev, curr)
    assert report.changed is True
    assert "DB_PASS" in report.removed_keys
    assert report.added_keys == []


def test_build_report_total_keys(snap_dir):
    curr = capture_snapshot(SECRETS_V2, "env", snap_dir)
    report = build_snapshot_report(None, curr)
    assert report.total_keys == len(SECRETS_V2)


def test_format_report_contains_environment(snap_dir):
    curr = capture_snapshot(SECRETS_V1, "staging", snap_dir)
    report = build_snapshot_report(None, curr)
    text = format_snapshot_report(report)
    assert "staging" in text


def test_format_report_no_changes_message(snap_dir):
    prev = capture_snapshot(SECRETS_V1, "prev", snap_dir)
    curr = capture_snapshot(SECRETS_V1, "curr", snap_dir)
    report = build_snapshot_report(prev, curr)
    text = format_snapshot_report(report)
    assert "No changes" in text


def test_format_report_lists_added_keys(snap_dir):
    prev = capture_snapshot(SECRETS_V1, "prev", snap_dir)
    curr = capture_snapshot(SECRETS_V2, "curr", snap_dir)
    report = build_snapshot_report(prev, curr)
    text = format_snapshot_report(report)
    assert "NEW_KEY" in text
    assert "Added" in text
