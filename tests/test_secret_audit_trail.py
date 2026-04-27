"""Tests for vaultpull.secret_audit_trail."""
import json
from pathlib import Path

import pytest

from vaultpull.secret_audit_trail import (
    TrailEntry,
    append_trail_entries,
    build_trail_entries,
    read_trail,
)


@pytest.fixture()
def trail_dir(tmp_path: Path) -> Path:
    return tmp_path / "trails"


def _make_entry(**kwargs) -> TrailEntry:
    defaults = dict(
        key="DB_PASSWORD",
        event="written",
        environment="staging",
        timestamp="2024-01-01T00:00:00+00:00",
        source_path="secret/app",
        changed=True,
        actor="ci",
    )
    defaults.update(kwargs)
    return TrailEntry(**defaults)


def test_trail_entry_roundtrip():
    entry = _make_entry()
    restored = TrailEntry.from_dict(entry.to_dict())
    assert restored == entry


def test_trail_entry_defaults_actor_none():
    entry = TrailEntry(
        key="X", event="fetched", environment="prod",
        timestamp="t", source_path="s",
    )
    assert entry.actor is None
    assert entry.changed is False


def test_append_creates_file(trail_dir: Path):
    entries = [_make_entry()]
    append_trail_entries(entries, trail_dir)
    trail_file = trail_dir / "audit_trail_staging.jsonl"
    assert trail_file.exists()


def test_append_valid_jsonl(trail_dir: Path):
    entries = [_make_entry(key="A"), _make_entry(key="B")]
    append_trail_entries(entries, trail_dir)
    lines = (trail_dir / "audit_trail_staging.jsonl").read_text().splitlines()
    assert len(lines) == 2
    data = json.loads(lines[0])
    assert data["key"] == "A"


def test_append_empty_does_not_create_file(trail_dir: Path):
    append_trail_entries([], trail_dir)
    assert not any(trail_dir.glob("*.jsonl")) if trail_dir.exists() else True


def test_read_trail_missing_file(trail_dir: Path):
    assert read_trail(trail_dir, "prod") == []


def test_read_trail_returns_entries(trail_dir: Path):
    entries = [_make_entry(key="K1"), _make_entry(key="K2")]
    append_trail_entries(entries, trail_dir)
    result = read_trail(trail_dir, "staging")
    assert len(result) == 2
    assert result[0].key == "K1"
    assert result[1].key == "K2"


def test_read_trail_skips_corrupt_lines(trail_dir: Path):
    trail_dir.mkdir(parents=True)
    f = trail_dir / "audit_trail_staging.jsonl"
    f.write_text('{"key": "A", "event": "fetched", "environment": "staging", "timestamp": "t", "source_path": "s"}\nnot-json\n')
    result = read_trail(trail_dir, "staging")
    assert len(result) == 1


def test_build_trail_entries_events():
    secrets = {"A": "1", "B": "2", "C": "3"}
    entries = build_trail_entries(
        secrets=secrets,
        changed_keys={"A"},
        skipped_keys={"C"},
        environment="dev",
        source_path="secret/app",
        actor="alice",
    )
    by_key = {e.key: e for e in entries}
    assert by_key["A"].event == "written"
    assert by_key["A"].changed is True
    assert by_key["B"].event == "fetched"
    assert by_key["B"].changed is False
    assert by_key["C"].event == "skipped"


def test_build_trail_entries_actor(trail_dir: Path):
    entries = build_trail_entries(
        secrets={"X": "v"},
        changed_keys=set(),
        skipped_keys=set(),
        environment="prod",
        source_path="s",
        actor="bot",
    )
    assert entries[0].actor == "bot"
