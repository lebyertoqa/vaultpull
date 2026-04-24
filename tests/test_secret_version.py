"""Tests for vaultpull.secret_version."""
import json
import pytest
from pathlib import Path

from vaultpull.secret_version import (
    load_versions,
    save_versions,
    build_version_report,
    format_version_report,
    VersionReport,
)


@pytest.fixture
def base_dir(tmp_path):
    return str(tmp_path)


def test_load_versions_missing_file(base_dir):
    result = load_versions(base_dir, "prod")
    assert result == {}


def test_save_and_load_versions(base_dir):
    versions = {"secret/db": 3, "secret/api": 1}
    save_versions(base_dir, "prod", versions)
    loaded = load_versions(base_dir, "prod")
    assert loaded == versions


def test_load_versions_corrupt_file(base_dir, tmp_path):
    vfile = tmp_path / ".vaultpull_versions_prod.json"
    vfile.write_text("not-json")
    result = load_versions(str(tmp_path), "prod")
    assert result == {}


def test_save_creates_parent_dirs(tmp_path):
    nested = str(tmp_path / "a" / "b")
    save_versions(nested, "staging", {"secret/x": 2})
    loaded = load_versions(nested, "staging")
    assert loaded == {"secret/x": 2}


def test_build_version_report_all_new():
    fetched = {"secret/db": 1, "secret/api": 2}
    previous = {}
    report = build_version_report("dev", fetched, previous)
    assert report.environment == "dev"
    assert report.total == 2
    assert set(report.upgraded) == {"secret/db", "secret/api"}
    assert report.unchanged == []


def test_build_version_report_some_unchanged():
    fetched = {"secret/db": 1, "secret/api": 3}
    previous = {"secret/db": 1, "secret/api": 2}
    report = build_version_report("prod", fetched, previous)
    assert "secret/api" in report.upgraded
    assert "secret/db" in report.unchanged


def test_build_version_report_all_unchanged():
    fetched = {"secret/db": 5}
    previous = {"secret/db": 5}
    report = build_version_report("prod", fetched, previous)
    assert report.upgraded == []
    assert "secret/db" in report.unchanged


def test_format_version_report_contains_environment():
    fetched = {"secret/db": 2}
    previous = {"secret/db": 1}
    report = build_version_report("staging", fetched, previous)
    output = format_version_report(report)
    assert "staging" in output
    assert "Upgraded" in output
    assert "secret/db" in output


def test_format_version_report_no_upgrades():
    fetched = {"secret/key": 1}
    previous = {"secret/key": 1}
    report = build_version_report("prod", fetched, previous)
    output = format_version_report(report)
    assert "Unchanged   : 1" in output
    assert "Upgraded    : 0" in output
