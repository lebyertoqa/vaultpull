"""Write fetched secrets into a .env file."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

_SAFE_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _quote_value(value: str) -> str:
    """Wrap value in double-quotes if it contains whitespace or special chars."""
    if re.search(r"[\s\"'\\#]", value):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value


def secrets_to_env_lines(secrets: dict[str, Any]) -> list[str]:
    """Convert a secrets dict to a list of KEY=VALUE lines."""
    lines: list[str] = []
    for key, raw_value in secrets.items():
        if not _SAFE_KEY_RE.match(key):
            raise ValueError(
                f"Secret key '{key}' is not a valid environment variable name."
            )
        value = str(raw_value)
        lines.append(f"{key}={_quote_value(value)}")
    return lines


def write_env_file(
    secrets: dict[str, Any],
    output_path: str | os.PathLike = ".env",
    overwrite: bool = True,
) -> Path:
    """Persist *secrets* to *output_path* as a .env file.

    Args:
        secrets:     Flat key/value mapping from Vault.
        output_path: Destination file path (default: ``.env``).
        overwrite:   If ``False`` and file exists, raise ``FileExistsError``.

    Returns:
        Resolved :class:`pathlib.Path` of the written file.
    """
    dest = Path(output_path).resolve()
    if not overwrite and dest.exists():
        raise FileExistsError(
            f"'{dest}' already exists. Pass overwrite=True to replace it."
        )

    lines = secrets_to_env_lines(secrets)
    content = "\n".join(lines) + "\n"
    dest.write_text(content, encoding="utf-8")
    return dest
