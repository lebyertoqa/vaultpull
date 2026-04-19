"""Tests for vaultpull.rollback."""

import os
from pathlib import Path

import pytest

from vaultpull.rollback import (
    backup_env_file,
    list_backups,
    prune_backups,
    restore_env_file,
)


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("KEY=value\n")
    return str(p)


def test_backup_creates_file(env_file):
    backup = backup_env_file(env_file)
    assert backup is not None
    assert Path(backup).exists()
    assert Path(backup).read_text() == "KEY=value\n"


def test_backup_missing_source(tmp_path):
    result = backup_env_file(str(tmp_path / "nonexistent.env"))
    assert result is None


def test_restore_replaces_file(env_file):
    backup = backup_env_file(env_file)
    Path(env_file).write_text("KEY=changed\n")
    restore_env_file(backup, env_file)
    assert Path(env_file).read_text() == "KEY=value\n"


def test_restore_missing_backup(tmp_path, env_file):
    with pytest.raises(FileNotFoundError, match="Backup not found"):
        restore_env_file(str(tmp_path / "ghost.bak"), env_file)


def test_list_backups_empty(env_file):
    assert list_backups(env_file) == []


def test_list_backups_multiple(env_file):
    b1 = backup_env_file(env_file)
    b2 = backup_env_file(env_file)
    backups = list_backups(env_file)
    assert len(backups) == 2
    assert b1 in backups and b2 in backups


def test_prune_keeps_most_recent(env_file):
    for _ in range(4):
        backup_env_file(env_file)
    deleted = prune_backups(env_file, keep=2)
    assert len(deleted) == 2
    remaining = list_backups(env_file)
    assert len(remaining) == 2
    for d in deleted:
        assert not Path(d).exists()


def test_prune_nothing_to_delete(env_file):
    backup_env_file(env_file)
    deleted = prune_backups(env_file, keep=5)
    assert deleted == []
