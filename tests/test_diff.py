"""Tests for vaultpull.diff module."""

import os
import pytest

from vaultpull.diff import compute_diff, DiffResult, _parse_env_file


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(
        'DB_HOST="localhost"\n'
        'DB_PORT="5432"\n'
        '# a comment\n'
        'API_KEY="oldsecret"\n'
    )
    return str(p)


def test_parse_env_file_basic(env_file):
    result = _parse_env_file(env_file)
    assert result["DB_HOST"] == "localhost"
    assert result["DB_PORT"] == "5432"
    assert result["API_KEY"] == "oldsecret"
    assert len(result) == 3


def test_parse_env_file_missing():
    result = _parse_env_file("/nonexistent/.env")
    assert result == {}


def test_compute_diff_added(env_file):
    incoming = {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "oldsecret", "NEW_KEY": "val"}
    diff = compute_diff(env_file, incoming)
    assert "NEW_KEY" in diff.added
    assert diff.has_changes


def test_compute_diff_changed(env_file):
    incoming = {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "newsecret"}
    diff = compute_diff(env_file, incoming)
    assert "API_KEY" in diff.changed
    assert diff.has_changes


def test_compute_diff_removed(env_file):
    incoming = {"DB_HOST": "localhost", "DB_PORT": "5432"}
    diff = compute_diff(env_file, incoming)
    assert "API_KEY" in diff.removed
    assert diff.has_changes


def test_compute_diff_unchanged(env_file):
    incoming = {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "oldsecret"}
    diff = compute_diff(env_file, incoming)
    assert not diff.has_changes
    assert set(diff.unchanged) == {"DB_HOST", "DB_PORT", "API_KEY"}


def test_compute_diff_no_existing_file(tmp_path):
    path = str(tmp_path / ".env")
    incoming = {"FOO": "bar", "BAZ": "qux"}
    diff = compute_diff(path, incoming)
    assert set(diff.added) == {"FOO", "BAZ"}
    assert diff.changed == []
    assert diff.removed == []
    assert diff.has_changes
