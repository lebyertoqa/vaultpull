"""Tests for vaultpull.dotenv_writer."""

from __future__ import annotations

import pytest

from vaultpull.dotenv_writer import secrets_to_env_lines, write_env_file


SIMPLE_SECRETS = {"DB_HOST": "localhost", "DB_PORT": "5432", "APP_ENV": "production"}


def test_secrets_to_env_lines_simple():
    lines = secrets_to_env_lines(SIMPLE_SECRETS)
    assert "DB_HOST=localhost" in lines
    assert "DB_PORT=5432" in lines
    assert "APP_ENV=production" in lines


def test_secrets_to_env_lines_quotes_whitespace():
    lines = secrets_to_env_lines({"SECRET_KEY": "hello world"})
    assert lines == ['SECRET_KEY="hello world"']


def test_secrets_to_env_lines_quotes_special_chars():
    lines = secrets_to_env_lines({"PW": 'p@ss"word'})
    assert lines == ['PW="p@ss\\"word"']


def test_secrets_to_env_lines_invalid_key():
    with pytest.raises(ValueError, match="not a valid environment variable name"):
        secrets_to_env_lines({"123BAD": "value"})


def test_secrets_to_env_lines_invalid_key_hyphen():
    with pytest.raises(ValueError):
        secrets_to_env_lines({"MY-KEY": "value"})


def test_secrets_to_env_lines_empty_value():
    """Empty string values should produce a line with an empty quoted value."""
    lines = secrets_to_env_lines({"EMPTY_VAR": ""})
    assert lines == ['EMPTY_VAR=""']


def test_secrets_to_env_lines_empty_dict():
    """An empty secrets dict should produce an empty list of lines."""
    lines = secrets_to_env_lines({})
    assert lines == []


def test_write_env_file_creates_file(tmp_path):
    dest = tmp_path / ".env"
    result = write_env_file(SIMPLE_SECRETS, output_path=dest)
    assert result == dest
    content = dest.read_text()
    assert "DB_HOST=localhost" in content
    assert content.endswith("\n")


def test_write_env_file_overwrite_false_raises(tmp_path):
    dest = tmp_path / ".env"
    dest.write_text("EXISTING=1\n")
    with pytest.raises(FileExistsError):
        write_env_file(SIMPLE_SECRETS, output_path=dest, overwrite=False)


def test_write_env_file_overwrite_true_replaces(tmp_path):
    dest = tmp_path / ".env"
    dest.write_text("OLD=value\n")
    write_env_file({"NEW_KEY": "new_value"}, output_path=dest, overwrite=True)
    content = dest.read_text()
    assert "OLD" not in content
    assert "NEW_KEY=new_value" in content
