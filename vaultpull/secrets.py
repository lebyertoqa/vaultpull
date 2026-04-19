"""Fetch secrets from HashiCorp Vault."""

from __future__ import annotations

from typing import Any

import hvac

from vaultpull.config import VaultConfig


class VaultClientError(Exception):
    """Raised when Vault communication fails."""


def _build_client(config: VaultConfig) -> hvac.Client:
    client = hvac.Client(url=config.address, token=config.token)
    if not client.is_authenticated():
        raise VaultClientError(
            f"Vault authentication failed for address '{config.address}'. "
            "Check VAULT_TOKEN or vault_token in config."
        )
    return client


def fetch_secrets(config: VaultConfig, path: str) -> dict[str, Any]:
    """Return key/value pairs stored at *path* in Vault KV v2.

    Args:
        config: Validated VaultConfig instance.
        path:   Secret path relative to the KV mount (e.g. ``myapp/prod``).

    Returns:
        A flat ``{key: value}`` dictionary of the secret's data.

    Raises:
        VaultClientError: On authentication or read failures.
    """
    client = _build_client(config)
    try:
        response = client.secrets.kv.v2.read_secret_version(
            path=path,
            mount_point=config.mount_point,
            raise_on_deleted_version=True,
        )
    except Exception as exc:  # hvac raises generic Exception subclasses
        raise VaultClientError(f"Failed to read secret at '{path}': {exc}") from exc

    data: dict[str, Any] = response["data"]["data"]
    return data
