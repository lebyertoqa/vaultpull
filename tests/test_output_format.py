"""Tests for vaultpull.output_format."""
import json
import pytest

from vaultpull.output_format import (
    OutputFormat,
    format_json,
    format_table,
    format_text,
    render,
)


def test_format_text_all_categories():
    out = format_text(["A"], ["B"], ["C"])
    assert "Added" in out
    assert "Changed" in out
    assert "Skipped" in out


def test_format_text_no_changes():
    out = format_text([], [], [])
    assert out == "No changes."


def test_format_text_with_error():
    out = format_text([], [], [], error="boom")
    assert "Error: boom" in out


def test_format_json_structure():
    out = format_json(["KEY1"], [], ["KEY2"])
    data = json.loads(out)
    assert data["added"] == ["KEY1"]
    assert data["skipped"] == ["KEY2"]
    assert data["changed"] == []
    assert "error" not in data


def test_format_json_with_error():
    out = format_json([], [], [], error="oops")
    data = json.loads(out)
    assert data["error"] == "oops"


def test_format_table_contains_keys():
    out = format_table(["FOO"], ["BAR"], [])
    assert "FOO" in out
    assert "BAR" in out
    assert "added" in out
    assert "changed" in out


def test_format_table_no_changes():
    out = format_table([], [], [])
    assert out == "No changes."


def test_format_table_with_error():
    out = format_table(["X"], [], [], error="fail")
    assert "Error: fail" in out


def test_render_dispatches_json():
    out = render(OutputFormat.JSON, ["K"], [], [])
    data = json.loads(out)
    assert "added" in data


def test_render_dispatches_table():
    out = render(OutputFormat.TABLE, [], ["K"], [])
    assert "K" in out
    assert "changed" in out


def test_render_dispatches_text():
    out = render(OutputFormat.TEXT, [], [], ["S"])
    assert "Skipped" in out
