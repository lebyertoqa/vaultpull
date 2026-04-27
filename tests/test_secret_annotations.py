"""Tests for vaultpull.secret_annotations."""

import pytest

from vaultpull.secret_annotations import (
    AnnotationConfig,
    AnnotationReport,
    _split_pairs,
    annotate_secrets,
    build_annotation_report,
    format_annotation_report,
    load_annotation_config,
)


# ---------------------------------------------------------------------------
# _split_pairs
# ---------------------------------------------------------------------------

def test_split_pairs_basic():
    result = _split_pairs("owner=team-a,env=prod")
    assert result == {"owner": "team-a", "env": "prod"}


def test_split_pairs_empty():
    assert _split_pairs("") == {}


def test_split_pairs_ignores_token_without_equals():
    result = _split_pairs("owner=team-a,badtoken,env=prod")
    assert "badtoken" not in result
    assert result["owner"] == "team-a"
    assert result["env"] == "prod"


# ---------------------------------------------------------------------------
# load_annotation_config
# ---------------------------------------------------------------------------

def test_load_defaults_no_section():
    cfg = load_annotation_config()
    assert cfg.annotations == {}
    assert cfg.per_key == {}
    assert cfg.environment == "default"


def test_load_from_dict():
    section = {
        "annotations": "owner=devops,tier=critical",
        "annotate.DB_PASSWORD": "sensitivity=high,rotate=true",
    }
    cfg = load_annotation_config(section, environment="staging")
    assert cfg.annotations == {"owner": "devops", "tier": "critical"}
    assert cfg.per_key["DB_PASSWORD"] == {"sensitivity": "high", "rotate": "true"}
    assert cfg.environment == "staging"


def test_load_from_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_ANNOTATIONS", "owner=ci")
    cfg = load_annotation_config()
    assert cfg.annotations == {"owner": "ci"}


def test_dict_takes_precedence_over_env(monkeypatch):
    monkeypatch.setenv("VAULTPULL_ANNOTATIONS", "owner=ci")
    cfg = load_annotation_config({"annotations": "owner=devops"})
    assert cfg.annotations["owner"] == "devops"


# ---------------------------------------------------------------------------
# annotate_secrets
# ---------------------------------------------------------------------------

def test_annotate_secrets_applies_global():
    cfg = load_annotation_config({"annotations": "env=prod"})
    result = annotate_secrets({"API_KEY": "secret"}, cfg)
    assert result["API_KEY"]["value"] == "secret"
    assert result["API_KEY"]["annotations"]["env"] == "prod"


def test_annotate_secrets_per_key_overrides_global():
    section = {
        "annotations": "owner=team-a",
        "annotate.DB_PASS": "owner=dba,sensitivity=high",
    }
    cfg = load_annotation_config(section)
    result = annotate_secrets({"DB_PASS": "s3cr3t", "OTHER": "val"}, cfg)
    assert result["DB_PASS"]["annotations"]["owner"] == "dba"
    assert result["DB_PASS"]["annotations"]["sensitivity"] == "high"
    assert result["OTHER"]["annotations"]["owner"] == "team-a"


def test_annotate_secrets_empty():
    cfg = load_annotation_config()
    result = annotate_secrets({}, cfg)
    assert result == {}


# ---------------------------------------------------------------------------
# build_annotation_report / format_annotation_report
# ---------------------------------------------------------------------------

def test_build_report_no_annotations():
    cfg = load_annotation_config(environment="dev")
    report = build_annotation_report({"KEY": "val"}, cfg)
    assert report.total == 1
    assert report.annotated == 0
    assert report.annotation_keys == []
    assert report.environment == "dev"


def test_build_report_with_annotations():
    section = {"annotations": "owner=ops,tier=1"}
    cfg = load_annotation_config(section, environment="prod")
    report = build_annotation_report({"A": "1", "B": "2"}, cfg)
    assert report.total == 2
    assert report.annotated == 2
    assert "owner" in report.annotation_keys
    assert "tier" in report.annotation_keys


def test_format_report_contains_environment():
    cfg = load_annotation_config(environment="qa")
    report = build_annotation_report({"X": "y"}, cfg)
    text = format_annotation_report(report)
    assert "qa" in text
    assert "Total secrets" in text
