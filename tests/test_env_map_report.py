"""Tests for vaultpull.env_map_report."""
import pytest

from vaultpull.secret_env_map import EnvMapConfig
from vaultpull.env_map_report import (
    EnvMapReport,
    build_env_map_report,
    format_env_map_report,
)


@pytest.fixture
def cfg_with_mapping():
    return EnvMapConfig(
        mappings={"secret/app": "APP"},
        strip_prefix=False,
        uppercase=True,
    )


def test_build_report_empty(cfg_with_mapping):
    report = build_env_map_report({}, "secret/app", cfg_with_mapping)
    assert report.total == 0
    assert report.renamed == 0


def test_build_report_with_mapping(cfg_with_mapping):
    secrets = {"db_host": "localhost", "db_port": "5432"}
    report = build_env_map_report(secrets, "secret/app", cfg_with_mapping)
    assert report.total == 2
    assert report.renamed == 2
    mapped_keys = {m["mapped"] for m in report.mappings}
    assert "APP_DB_HOST" in mapped_keys
    assert "APP_DB_PORT" in mapped_keys


def test_build_report_no_rename():
    cfg = EnvMapConfig(mappings={}, strip_prefix=False, uppercase=False)
    secrets = {"key": "val"}
    report = build_env_map_report(secrets, "secret/app", cfg)
    assert report.renamed == 0
    assert report.mappings[0]["original"] == report.mappings[0]["mapped"]


def test_build_report_environment_label(cfg_with_mapping):
    report = build_env_map_report({}, "secret/app", cfg_with_mapping, environment="prod")
    assert report.environment == "prod"
    assert report.path == "secret/app"


def test_format_report_contains_environment(cfg_with_mapping):
    secrets = {"token": "abc"}
    report = build_env_map_report(secrets, "secret/app", cfg_with_mapping, environment="staging")
    text = format_env_map_report(report)
    assert "staging" in text
    assert "secret/app" in text


def test_format_report_shows_arrow(cfg_with_mapping):
    secrets = {"token": "abc"}
    report = build_env_map_report(secrets, "secret/app", cfg_with_mapping)
    text = format_env_map_report(report)
    assert "->" in text


def test_format_report_shows_equal_when_no_rename():
    cfg = EnvMapConfig(mappings={}, strip_prefix=False, uppercase=False)
    secrets = {"key": "val"}
    report = build_env_map_report(secrets, "secret/app", cfg)
    text = format_env_map_report(report)
    assert "==" in text
