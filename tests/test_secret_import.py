"""Tests for vaultpull.secret_import and vaultpull.import_report."""
import os
import pytest

from vaultpull.secret_import import (
    ImportConfig,
    load_import_config,
    import_env_file,
)
from vaultpull.import_report import build_import_report, format_import_report


# ---------------------------------------------------------------------------
# load_import_config
# ---------------------------------------------------------------------------

def test_load_defaults_no_section():
    cfg = load_import_config()
    assert cfg.source_file == ".env.import"
    assert cfg.prefix == ""
    assert cfg.overwrite is False
    assert cfg.skip_invalid is True
    assert cfg.encoding == "utf-8"


def test_load_from_dict():
    cfg = load_import_config({
        "source_file": "secrets.env",
        "prefix": "APP_",
        "overwrite": "true",
        "skip_invalid": "false",
        "encoding": "latin-1",
    })
    assert cfg.source_file == "secrets.env"
    assert cfg.prefix == "APP_"
    assert cfg.overwrite is True
    assert cfg.skip_invalid is False
    assert cfg.encoding == "latin-1"


def test_load_from_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_IMPORT_SOURCE", "prod.env")
    monkeypatch.setenv("VAULTPULL_IMPORT_PREFIX", "PROD_")
    monkeypatch.setenv("VAULTPULL_IMPORT_OVERWRITE", "1")
    cfg = load_import_config()
    assert cfg.source_file == "prod.env"
    assert cfg.prefix == "PROD_"
    assert cfg.overwrite is True


# ---------------------------------------------------------------------------
# import_env_file
# ---------------------------------------------------------------------------

@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env.import"
    p.write_text("DB_HOST=localhost\nDB_PORT=5432\n# comment\nBAD KEY=nope\n")
    return p


def test_import_basic(env_file):
    cfg = ImportConfig(source_file=str(env_file))
    result = import_env_file(cfg)
    assert result.imported == {"DB_HOST": "localhost", "DB_PORT": "5432"}
    assert result.total == 2


def test_import_with_prefix(env_file):
    cfg = ImportConfig(source_file=str(env_file), prefix="APP_")
    result = import_env_file(cfg)
    assert "APP_DB_HOST" in result.imported
    assert "APP_DB_PORT" in result.imported


def test_import_skips_invalid_key(env_file):
    cfg = ImportConfig(source_file=str(env_file), skip_invalid=True)
    result = import_env_file(cfg)
    assert "BAD KEY" not in result.imported
    assert "BAD KEY" in result.skipped


def test_import_error_on_invalid_key(env_file):
    cfg = ImportConfig(source_file=str(env_file), skip_invalid=False)
    result = import_env_file(cfg)
    assert any("BAD KEY" in e for e in result.errors)


def test_import_missing_file(tmp_path):
    cfg = ImportConfig(source_file=str(tmp_path / "missing.env"))
    result = import_env_file(cfg)
    assert result.total == 0
    assert result.errors


def test_import_no_overwrite(env_file):
    cfg = ImportConfig(source_file=str(env_file), overwrite=False)
    result = import_env_file(cfg, existing={"DB_HOST": "remotehost"})
    assert "DB_HOST" not in result.imported
    assert "DB_HOST" in result.skipped
    assert result.imported.get("DB_PORT") == "5432"


def test_import_overwrite(env_file):
    cfg = ImportConfig(source_file=str(env_file), overwrite=True)
    result = import_env_file(cfg, existing={"DB_HOST": "remotehost"})
    assert result.imported.get("DB_HOST") == "localhost"


# ---------------------------------------------------------------------------
# import_report
# ---------------------------------------------------------------------------

def test_build_report_basic(env_file):
    cfg = ImportConfig(source_file=str(env_file))
    result = import_env_file(cfg)
    report = build_import_report(cfg, result, environment="test")
    assert report.environment == "test"
    assert report.imported == 2
    assert report.has_errors is False


def test_format_report_contains_environment(env_file):
    cfg = ImportConfig(source_file=str(env_file))
    result = import_env_file(cfg)
    report = build_import_report(cfg, result, environment="staging")
    text = format_import_report(report)
    assert "staging" in text
    assert "Imported" in text


def test_format_report_shows_errors(tmp_path):
    cfg = ImportConfig(source_file=str(tmp_path / "no.env"))
    result = import_env_file(cfg)
    report = build_import_report(cfg, result, environment="prod")
    text = format_import_report(report)
    assert "Errors" in text
    assert "not found" in text
