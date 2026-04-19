"""Tests for the CLI entry point."""
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from vaultpull.cli import main


FAKE_SECRETS = {"DB_PASSWORD": "s3cr3t", "API_KEY": "abc123"}


def _good_config():
    cfg = MagicMock()
    return cfg


@patch("vaultpull.cli.write_env_file", return_value=True)
@patch("vaultpull.cli.fetch_secrets", return_value=FAKE_SECRETS)
@patch("vaultpull.cli.validate", return_value=[])
@patch("vaultpull.cli.load_config")
def test_main_success(mock_load, mock_validate, mock_fetch, mock_write):
    runner = CliRunner()
    result = runner.invoke(main, ["--config", "vaultpull.yaml", "--output", ".env"])
    assert result.exit_code == 0
    assert "Wrote 2 secret(s)" in result.output
    mock_write.assert_called_once()


@patch("vaultpull.cli.write_env_file", return_value=False)
@patch("vaultpull.cli.fetch_secrets", return_value=FAKE_SECRETS)
@patch("vaultpull.cli.validate", return_value=[])
@patch("vaultpull.cli.load_config")
def test_main_no_overwrite(mock_load, mock_validate, mock_fetch, mock_write):
    runner = CliRunner()
    result = runner.invoke(main, ["--no-overwrite"])
    assert result.exit_code == 0
    assert "skip" in result.output


@patch("vaultpull.cli.load_config", side_effect=FileNotFoundError)
def test_main_config_not_found(mock_load):
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 1
    assert "not found" in result.output


@patch("vaultpull.cli.validate", return_value=["vault_addr is required"])
@patch("vaultpull.cli.load_config")
def test_main_validation_errors(mock_load, mock_validate):
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 1
    assert "vault_addr is required" in result.output


@patch("vaultpull.cli.fetch_secrets", side_effect=__import__("vaultpull.secrets", fromlist=["VaultClientError"]).VaultClientError("connection refused"))
@patch("vaultpull.cli.validate", return_value=[])
@patch("vaultpull.cli.load_config")
def test_main_vault_error(mock_load, mock_validate, mock_fetch):
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 1
    assert "connection refused" in result.output


@patch("vaultpull.cli.fetch_secrets", return_value=FAKE_SECRETS)
@patch("vaultpull.cli.validate", return_value=[])
@patch("vaultpull.cli.load_config")
def test_main_dry_run(mock_load, mock_validate, mock_fetch):
    runner = CliRunner()
    result = runner.invoke(main, ["--dry-run"])
    assert result.exit_code == 0
    assert "DB_PASSWORD" in result.output
    assert "API_KEY" in result.output
