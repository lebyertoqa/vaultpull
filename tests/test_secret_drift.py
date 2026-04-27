"""Tests for vaultpull.secret_drift."""
import pytest

from vaultpull.secret_drift import (
    DriftRecord,
    DriftReport,
    _parse_env_file,
    compute_drift,
    format_drift_report,
)


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(
        "DB_HOST=localhost\n"
        "DB_PASS=\"secret123\"\n"
        "OLD_KEY=gone\n"
        "# comment line\n"
        "UNCHANGED=same\n"
    )
    return str(p)


def test_parse_env_file_basic(env_file):
    result = _parse_env_file(env_file)
    assert result["DB_HOST"] == "localhost"
    assert result["DB_PASS"] == "secret123"
    assert result["OLD_KEY"] == "gone"
    assert "# comment line" not in result


def test_parse_env_file_missing():
    result = _parse_env_file("/nonexistent/.env")
    assert result == {}


def test_compute_drift_added(env_file):
    vault = {"DB_HOST": "localhost", "DB_PASS": "secret123", "UNCHANGED": "same", "NEW_KEY": "newval"}
    report = compute_drift(vault, env_file)
    statuses = {r.key: r.status for r in report.records}
    assert statuses["NEW_KEY"] == "added"


def test_compute_drift_removed(env_file):
    vault = {"DB_HOST": "localhost", "DB_PASS": "secret123", "UNCHANGED": "same"}
    report = compute_drift(vault, env_file)
    statuses = {r.key: r.status for r in report.records}
    assert statuses["OLD_KEY"] == "removed"


def test_compute_drift_changed(env_file):
    vault = {"DB_HOST": "newhost", "DB_PASS": "secret123", "OLD_KEY": "gone", "UNCHANGED": "same"}
    report = compute_drift(vault, env_file)
    statuses = {r.key: r.status for r in report.records}
    assert statuses["DB_HOST"] == "changed"


def test_compute_drift_ok(env_file):
    vault = {"DB_HOST": "localhost", "DB_PASS": "secret123", "OLD_KEY": "gone", "UNCHANGED": "same"}
    report = compute_drift(vault, env_file)
    statuses = {r.key: r.status for r in report.records}
    assert statuses["UNCHANGED"] == "ok"
    assert statuses["DB_HOST"] == "ok"


def test_has_drift_true(env_file):
    vault = {"DB_HOST": "localhost", "DB_PASS": "secret123", "UNCHANGED": "same", "EXTRA": "x"}
    report = compute_drift(vault, env_file)
    assert report.has_drift is True


def test_has_drift_false(env_file):
    vault = {"DB_HOST": "localhost", "DB_PASS": "secret123", "OLD_KEY": "gone", "UNCHANGED": "same"}
    report = compute_drift(vault, env_file)
    assert report.has_drift is False


def test_environment_label(env_file):
    report = compute_drift({}, env_file, environment="staging")
    assert report.environment == "staging"


def test_format_no_drift(env_file):
    vault = {"DB_HOST": "localhost", "DB_PASS": "secret123", "OLD_KEY": "gone", "UNCHANGED": "same"}
    report = compute_drift(vault, env_file)
    text = format_drift_report(report)
    assert "No drift" in text


def test_format_with_drift(env_file):
    vault = {"DB_HOST": "changed", "UNCHANGED": "same"}
    report = compute_drift(vault, env_file, environment="prod")
    text = format_drift_report(report)
    assert "prod" in text
    assert "CHANGED" in text or "changed" in text.lower()
    assert "drifted" in text
