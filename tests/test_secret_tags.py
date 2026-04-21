"""Tests for vaultpull/secret_tags.py"""
import pytest
from vaultpull.secret_tags import (
    TagConfig,
    load_tag_config,
    extract_tags,
    secret_matches_tags,
    apply_tag_filter,
)


SECRET_PROD = {"value": "s3cr3t", "tag:env": "prod", "tag:team": "platform"}
SECRET_DEV = {"value": "devval", "tag:env": "dev"}
SECRET_NO_TAGS = {"value": "plain"}


def test_load_defaults_no_section():
    cfg = load_tag_config()
    assert cfg.required_tags == []
    assert cfg.excluded_tags == []
    assert cfg.tag_prefix == "tag:"
    assert cfg.strict is False


def test_load_from_dict():
    cfg = load_tag_config({"required_tags": "env,team", "excluded_tags": "deprecated", "strict": "true"})
    assert cfg.required_tags == ["env", "team"]
    assert cfg.excluded_tags == ["deprecated"]
    assert cfg.strict is True


def test_extract_tags_basic():
    tags = extract_tags(SECRET_PROD)
    assert set(tags) == {"env", "team"}


def test_extract_tags_empty():
    assert extract_tags(SECRET_NO_TAGS) == []


def test_extract_tags_custom_prefix():
    secret = {"label:region": "us-east", "value": "x"}
    assert extract_tags(secret, tag_prefix="label:") == ["region"]


def test_secret_matches_no_constraints():
    cfg = TagConfig()
    assert secret_matches_tags(SECRET_PROD, cfg) is True
    assert secret_matches_tags(SECRET_NO_TAGS, cfg) is True


def test_secret_matches_required_tag_present():
    cfg = TagConfig(required_tags=["env"])
    assert secret_matches_tags(SECRET_PROD, cfg) is True


def test_secret_matches_required_tag_missing():
    cfg = TagConfig(required_tags=["team"])
    assert secret_matches_tags(SECRET_DEV, cfg) is False


def test_secret_matches_excluded_tag():
    cfg = TagConfig(excluded_tags=["env"])
    assert secret_matches_tags(SECRET_PROD, cfg) is False
    assert secret_matches_tags(SECRET_NO_TAGS, cfg) is True


def test_secret_strict_excludes_no_tags():
    cfg = TagConfig(strict=True)
    assert secret_matches_tags(SECRET_NO_TAGS, cfg) is False
    assert secret_matches_tags(SECRET_PROD, cfg) is True


def test_apply_tag_filter_required():
    secrets = {"a": SECRET_PROD, "b": SECRET_DEV, "c": SECRET_NO_TAGS}
    cfg = TagConfig(required_tags=["team"])
    result = apply_tag_filter(secrets, cfg)
    assert list(result.keys()) == ["a"]


def test_apply_tag_filter_strict():
    secrets = {"a": SECRET_PROD, "b": SECRET_NO_TAGS}
    cfg = TagConfig(strict=True)
    result = apply_tag_filter(secrets, cfg)
    assert "a" in result
    assert "b" not in result
