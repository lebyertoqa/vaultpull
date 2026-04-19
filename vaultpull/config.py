"""Configuration loader for vaultpull.

Reads settings from a .vaultpull.toml file in the current directory
or from environment variables as fallback.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib  # type: ignore


DEFAULT_CONFIG_FILE = ".vaultpull.toml"


@dataclass
class VaultConfig:
    vault_addr: str
    vault_token: str
    secret_path: str
    env_file: str = ".env"
    mount_point: str = "secret"
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "VaultConfig":
        vault = data.get("vault", {})
        return cls(
            vault_addr=vault.get("addr", os.environ.get("VAULT_ADDR", "")),
            vault_token=vault.get("token", os.environ.get("VAULT_TOKEN", "")),
            secret_path=vault.get("secret_path", ""),
            env_file=vault.get("env_file", ".env"),
            mount_point=vault.get("mount_point", "secret"),
            extra={k: v for k, v in data.items() if k != "vault"},
        )

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.vault_addr:
            errors.append("vault.addr is required (or set VAULT_ADDR env var)")
        if not self.vault_token:
            errors.append("vault.token is required (or set VAULT_TOKEN env var)")
        if not self.secret_path:
            errors.append("vault.secret_path is required")
        return errors


def load_config(config_path: str | Path | None = None) -> VaultConfig:
    """Load config from a TOML file, falling back to env vars."""
    path = Path(config_path) if config_path else Path(DEFAULT_CONFIG_FILE)

    if path.exists():
        with path.open("rb") as fh:
            data = tomllib.load(fh)
    else:
        data = {}

    return VaultConfig.from_dict(data)
