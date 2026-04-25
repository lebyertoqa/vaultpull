"""Tests for vaultpull.secret_snapshot."""
import json
import pytest
from pathlib import Path

from vaultpull.secret_snapshot import (
    _fingerprint,
    capture_snapshot,
    load_snapshot,
    snapshots_differ,
    Snapshot,
)


@pytest.fixture
def snap_dir(tmp_path: Path) -> Path:
    return tmp_path / "snapshots"


SECRETS = {"DB_PASS": "hunter2", "API_KEY": "abc123"}


def test_fingerprint_is_stable():
    assert _fingerprint(SECRETS) == _fingerprint(SECRETS)


def test_fingerprint_differs_on_value_change():
    modified = {**SECRETS, "DB_PASS": "changed"}
    assert _fingerprint(SECRETS) != _fingerprint(modified)


def test_capture_creates_file(snap_dir):
    snap = capture_snapshot(SECRETS, "production", snap_dir)
    path = snap_dir / "production.snapshot.json"
    assert path.exists()
    assert snap.environment == "production"
    assert sorted(SECRETS.keys()) == snap.keys


def test_capture_snapshot_fingerprint(snap_dir):
    snap = capture_snapshot(SECRETS, "staging", snap_dir)
    assert snap.fingerprint == _fingerprint(SECRETS)


def test_load_snapshot_roundtrip(snap_dir):
    capture_snapshot(SECRETS, "dev", snap_dir)
    loaded = load_snapshot("dev", snap_dir)
    assert loaded is not None
    assert loaded.environment == "dev"
    assert loaded.fingerprint == _fingerprint(SECRETS)


def test_load_snapshot_missing_returns_none(snap_dir):
    result = load_snapshot("nonexistent", snap_dir)
    assert result is None


def test_load_snapshot_corrupt_returns_none(snap_dir):
    snap_dir.mkdir(parents=True)
    (snap_dir / "bad.snapshot.json").write_text("not-json", encoding="utf-8")
    assert load_snapshot("bad", snap_dir) is None


def test_snapshots_differ_none_previous(snap_dir):
    snap = capture_snapshot(SECRETS, "env", snap_dir)
    assert snapshots_differ(None, snap) is True


def test_snapshots_differ_same(snap_dir):
    s1 = capture_snapshot(SECRETS, "env", snap_dir)
    s2 = capture_snapshot(SECRETS, "env2", snap_dir)
    assert snapshots_differ(s1, s2) is False


def test_snapshots_differ_changed(snap_dir):
    s1 = capture_snapshot(SECRETS, "env", snap_dir)
    s2 = capture_snapshot({"DB_PASS": "new"}, "env2", snap_dir)
    assert snapshots_differ(s1, s2) is True


def test_snapshot_to_dict_and_from_dict(snap_dir):
    original = capture_snapshot(SECRETS, "prod", snap_dir)
    restored = Snapshot.from_dict(original.to_dict())
    assert restored.environment == original.environment
    assert restored.fingerprint == original.fingerprint
    assert restored.keys == original.keys
