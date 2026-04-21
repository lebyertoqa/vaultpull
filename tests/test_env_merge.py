"""Tests for vaultpull.env_merge."""
import pytest

from vaultpull.env_merge import (
    MergeStrategy,
    MergeResult,
    merge_secrets,
    load_merge_strategy,
)


LOCAL = {"DB_HOST": "localhost", "DB_PORT": "5432", "APP_KEY": "old"}
VAULT = {"APP_KEY": "new", "SECRET_TOKEN": "abc123"}


# ---------------------------------------------------------------------------
# merge_secrets — OVERWRITE strategy
# ---------------------------------------------------------------------------

def test_overwrite_adds_new_key():
    result = merge_secrets(LOCAL, VAULT, MergeStrategy.OVERWRITE)
    assert "SECRET_TOKEN" in result.merged
    assert "SECRET_TOKEN" in result.added


def test_overwrite_updates_existing_key():
    result = merge_secrets(LOCAL, VAULT, MergeStrategy.OVERWRITE)
    assert result.merged["APP_KEY"] == "new"
    assert "APP_KEY" in result.updated


def test_overwrite_preserves_local_only_keys():
    result = merge_secrets(LOCAL, VAULT, MergeStrategy.OVERWRITE)
    assert result.merged["DB_HOST"] == "localhost"
    assert result.merged["DB_PORT"] == "5432"


def test_overwrite_no_conflicts():
    result = merge_secrets(LOCAL, VAULT, MergeStrategy.OVERWRITE)
    assert result.conflicts == []
    assert result.preserved == []


# ---------------------------------------------------------------------------
# merge_secrets — PRESERVE strategy
# ---------------------------------------------------------------------------

def test_preserve_keeps_local_value():
    result = merge_secrets(LOCAL, VAULT, MergeStrategy.PRESERVE)
    assert result.merged["APP_KEY"] == "old"
    assert "APP_KEY" in result.preserved


def test_preserve_still_adds_new_key():
    result = merge_secrets(LOCAL, VAULT, MergeStrategy.PRESERVE)
    assert result.merged["SECRET_TOKEN"] == "abc123"
    assert "SECRET_TOKEN" in result.added


def test_preserve_no_updated_entries():
    result = merge_secrets(LOCAL, VAULT, MergeStrategy.PRESERVE)
    assert result.updated == []


# ---------------------------------------------------------------------------
# merge_secrets — PROMPT strategy
# ---------------------------------------------------------------------------

def test_prompt_records_conflicts():
    result = merge_secrets(LOCAL, VAULT, MergeStrategy.PROMPT)
    assert result.has_conflicts
    keys = [c[0] for c in result.conflicts]
    assert "APP_KEY" in keys


def test_prompt_conflict_contains_both_values():
    result = merge_secrets(LOCAL, VAULT, MergeStrategy.PROMPT)
    conflict = next(c for c in result.conflicts if c[0] == "APP_KEY")
    assert conflict[1] == "old"   # local
    assert conflict[2] == "new"   # vault


def test_prompt_no_update_to_merged_for_conflicts():
    result = merge_secrets(LOCAL, VAULT, MergeStrategy.PROMPT)
    # merged should retain local value when conflict unresolved
    assert result.merged["APP_KEY"] == "old"


# ---------------------------------------------------------------------------
# identical values — no change recorded
# ---------------------------------------------------------------------------

def test_identical_value_not_in_updated_or_added():
    local = {"KEY": "same"}
    vault = {"KEY": "same"}
    result = merge_secrets(local, vault, MergeStrategy.OVERWRITE)
    assert result.added == []
    assert result.updated == []


# ---------------------------------------------------------------------------
# load_merge_strategy
# ---------------------------------------------------------------------------

def test_load_strategy_overwrite():
    assert load_merge_strategy("overwrite") == MergeStrategy.OVERWRITE


def test_load_strategy_preserve():
    assert load_merge_strategy("preserve") == MergeStrategy.PRESERVE


def test_load_strategy_prompt():
    assert load_merge_strategy("prompt") == MergeStrategy.PROMPT


def test_load_strategy_case_insensitive():
    assert load_merge_strategy("OVERWRITE") == MergeStrategy.OVERWRITE


def test_load_strategy_none_defaults_to_overwrite():
    assert load_merge_strategy(None) == MergeStrategy.OVERWRITE


def test_load_strategy_invalid_raises():
    with pytest.raises(ValueError, match="Unknown merge strategy"):
        load_merge_strategy("replace")
