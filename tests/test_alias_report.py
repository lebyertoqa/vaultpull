"""Tests for vaultpull/alias_report.py and alias_config_loader.py"""
import pytest
from vaultpull.path_alias import AliasConfig
from vaultpull.alias_report import AliasReport, build_alias_report, format_alias_report
from vaultpull.alias_config_loader import get_alias_config, describe_aliases


@pytest.fixture
def cfg_with_alias():
    return AliasConfig(aliases={"secret/app": "APP"}, strip_prefix=True, uppercase=True)


def test_build_report_empty(cfg_with_alias):
    report = build_alias_report({}, cfg_with_alias, environment="staging")
    assert report.total == 0
    assert report.renamed == 0
    assert report.environment == "staging"


def test_build_report_with_alias(cfg_with_alias):
    path_secrets = {"secret/app": {"db_pass": "s3cr3t", "api_key": "abc"}}
    report = build_alias_report(path_secrets, cfg_with_alias)
    assert report.total == 2
    # original keys are lowercase, resolved are APP_DB_PASS etc — all renamed
    assert report.renamed == 2


def test_build_report_no_alias_strip():
    cfg = AliasConfig(aliases={}, strip_prefix=True, uppercase=True)
    path_secrets = {"secret/svc": {"TOKEN": "xyz"}}
    report = build_alias_report(path_secrets, cfg)
    assert report.total == 1
    # original key already uppercase, no prefix added — not renamed
    assert report.renamed == 0


def test_format_report_contains_environment(cfg_with_alias):
    path_secrets = {"secret/app": {"pw": "x"}}
    report = build_alias_report(path_secrets, cfg_with_alias, environment="prod")
    text = format_alias_report(report)
    assert "prod" in text
    assert "APP_PW" in text


def test_format_report_no_keys(cfg_with_alias):
    report = build_alias_report({}, cfg_with_alias)
    text = format_alias_report(report)
    assert "(no keys)" in text


def test_get_alias_config_from_full_config():
    full_cfg = {"alias": {"aliases": {"secret/x": "X"}, "uppercase": "true"}}
    cfg = get_alias_config(full_cfg)
    assert cfg.aliases == {"secret/x": "X"}


def test_get_alias_config_missing_section():
    cfg = get_alias_config({})
    assert cfg.aliases == {}


def test_describe_aliases_no_aliases():
    cfg = AliasConfig(aliases={}, strip_prefix=True, uppercase=True)
    assert describe_aliases(cfg) == "No path aliases configured."


def test_describe_aliases_with_entries():
    cfg = AliasConfig(aliases={"secret/app": "APP", "secret/db": "DB"}, strip_prefix=True, uppercase=True)
    desc = describe_aliases(cfg)
    assert "secret/app -> APP" in desc
    assert "secret/db -> DB" in desc
