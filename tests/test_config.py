"""Tests for vaultpull.config module."""

import os
import textwrap
from pathlib import Path

import pytest

from vaultpull.config import VaultConfig, load_config


# ---------------------------------------------------------------------------
# VaultConfig.from_dict
# ---------------------------------------------------------------------------

def test_from_dict_full():
    data = {
        "vault": {
            "addr": "https://vault.example.com",
            "token": "s.abc123",
            "secret_path": "myapp/prod",
            "env_file": ".env.prod",
            "mount_point": "kv",
        }
    }
    cfg = VaultConfig.from_dict(data)
    assert cfg.vault_addr == "https://vault.example.com"
    assert cfg.vault_token == "s.abc123"
    assert cfg.secret_path == "myapp/prod"
    assert cfg.env_file == ".env.prod"
    assert cfg.mount_point == "kv"


def test_from_dict_falls_back_to_env(monkeypatch):
    monkeypatch.setenv("VAULT_ADDR", "https://env-vault.example.com")
    monkeypatch.setenv("VAULT_TOKEN", "s.envtoken")
    cfg = VaultConfig.from_dict({"vault": {"secret_path": "app/dev"}})
    assert cfg.vault_addr == "https://env-vault.example.com"
    assert cfg.vault_token == "s.envtoken"


def test_from_dict_defaults():
    cfg = VaultConfig.from_dict({})
    assert cfg.env_file == ".env"
    assert cfg.mount_point == "secret"


# ---------------------------------------------------------------------------
# VaultConfig.validate
# ---------------------------------------------------------------------------

def test_validate_passes():
    cfg = VaultConfig(
        vault_addr="https://vault.example.com",
        vault_token="s.tok",
        secret_path="app/prod",
    )
    assert cfg.validate() == []


def test_validate_missing_all():
    cfg = VaultConfig(vault_addr="", vault_token="", secret_path="")
    errors = cfg.validate()
    assert len(errors) == 3


# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------

def test_load_config_from_toml(tmp_path):
    toml_content = textwrap.dedent("""
        [vault]
        addr = "https://toml-vault.example.com"
        token = "s.tomltoken"
        secret_path = "service/staging"
    """)
    config_file = tmp_path / ".vaultpull.toml"
    config_file.write_text(toml_content)

    cfg = load_config(config_file)
    assert cfg.vault_addr == "https://toml-vault.example.com"
    assert cfg.secret_path == "service/staging"


def test_load_config_missing_file_returns_defaults(tmp_path):
    cfg = load_config(tmp_path / "nonexistent.toml")
    assert cfg.env_file == ".env"
    assert cfg.vault_addr == ""
