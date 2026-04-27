"""Tests for vaultpull.secret_ownership."""
import json
from pathlib import Path

import pytest

from vaultpull.secret_ownership import (
    OwnershipConfig,
    OwnershipRecord,
    assign_ownership,
    load_ownership_config,
    load_ownership_records,
    save_ownership_records,
)


@pytest.fixture
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


# --- load_ownership_config ---

def test_load_defaults_no_section():
    cfg = load_ownership_config()
    assert cfg.default_owner is None
    assert cfg.default_team is None
    assert cfg.default_contact is None
    assert cfg.tracked_keys == []


def test_load_from_dict():
    cfg = load_ownership_config({
        "default_owner": "alice",
        "default_team": "platform",
        "default_contact": "alice@example.com",
        "tracked_keys": "DB_PASS, API_KEY",
    })
    assert cfg.default_owner == "alice"
    assert cfg.default_team == "platform"
    assert cfg.default_contact == "alice@example.com"
    assert cfg.tracked_keys == ["DB_PASS", "API_KEY"]


def test_load_from_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_OWNER", "bob")
    monkeypatch.setenv("VAULTPULL_TEAM", "infra")
    monkeypatch.setenv("VAULTPULL_CONTACT", "bob@example.com")
    cfg = load_ownership_config()
    assert cfg.default_owner == "bob"
    assert cfg.default_team == "infra"
    assert cfg.default_contact == "bob@example.com"


def test_dict_overrides_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_OWNER", "env-owner")
    cfg = load_ownership_config({"default_owner": "dict-owner"})
    assert cfg.default_owner == "dict-owner"


# --- OwnershipRecord roundtrip ---

def test_record_roundtrip():
    rec = OwnershipRecord(key="DB_PASS", owner="alice", team="platform", contact="alice@example.com")
    assert OwnershipRecord.from_dict(rec.to_dict()) == rec


def test_record_optional_fields():
    rec = OwnershipRecord(key="API_KEY")
    d = rec.to_dict()
    assert d["owner"] is None
    assert d["team"] is None
    restored = OwnershipRecord.from_dict(d)
    assert restored.key == "API_KEY"


# --- save / load ---

def test_load_missing_file(base_dir):
    assert load_ownership_records(base_dir) == {}


def test_save_and_load(base_dir):
    records = {
        "DB_PASS": OwnershipRecord(key="DB_PASS", owner="alice", team="platform"),
        "API_KEY": OwnershipRecord(key="API_KEY", owner="bob"),
    }
    save_ownership_records(base_dir, records)
    loaded = load_ownership_records(base_dir)
    assert loaded["DB_PASS"].owner == "alice"
    assert loaded["API_KEY"].owner == "bob"


def test_load_skips_corrupt_lines(base_dir):
    path = base_dir / ".vaultpull" / "ownership.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text('{"key": "GOOD", "owner": "x"}\nnot-json\n')
    records = load_ownership_records(base_dir)
    assert "GOOD" in records
    assert len(records) == 1


# --- assign_ownership ---

def test_assign_all_keys_when_no_tracked():
    cfg = OwnershipConfig(default_owner="alice", default_team="ops")
    secrets = {"DB_PASS": "s3cr3t", "API_KEY": "key123"}
    result = assign_ownership(secrets, cfg)
    assert set(result.keys()) == {"DB_PASS", "API_KEY"}
    assert result["DB_PASS"].owner == "alice"


def test_assign_only_tracked_keys():
    cfg = OwnershipConfig(default_owner="alice", tracked_keys=["DB_PASS"])
    secrets = {"DB_PASS": "s3cr3t", "API_KEY": "key123"}
    result = assign_ownership(secrets, cfg)
    assert "DB_PASS" in result
    assert "API_KEY" not in result


def test_assign_preserves_existing():
    cfg = OwnershipConfig(default_owner="new-owner")
    existing = {"DB_PASS": OwnershipRecord(key="DB_PASS", owner="original")}
    secrets = {"DB_PASS": "val", "TOKEN": "tok"}
    result = assign_ownership(secrets, cfg, existing=existing)
    assert result["DB_PASS"].owner == "original"  # not overwritten
    assert result["TOKEN"].owner == "new-owner"


def test_assign_skips_missing_secrets():
    cfg = OwnershipConfig(tracked_keys=["MISSING_KEY"])
    secrets = {"DB_PASS": "val"}
    result = assign_ownership(secrets, cfg)
    assert "MISSING_KEY" not in result
