"""Load output-format configuration for vaultpull."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict

from vaultpull.output_format import OutputFormat

_SECTION = "output"


@dataclass
class OutputConfig:
    format: OutputFormat = OutputFormat.TEXT
    color: bool = True
    quiet: bool = False


def _bool_env(name: str, default: bool) -> bool:
    val = os.environ.get(name, "").strip().lower()
    if val in ("1", "true", "yes"):
        return True
    if val in ("0", "false", "no"):
        return False
    return default


def load_output_config(cfg: Dict[str, Any] | None = None) -> OutputConfig:
    """Build OutputConfig from an optional config dict section.

    Falls back to environment variables, then defaults.
    """
    section: Dict[str, Any] = (cfg or {}).get(_SECTION, {})

    raw_fmt = (
        section.get("format")
        or os.environ.get("VAULTPULL_OUTPUT_FORMAT", "")
    ).strip().lower()
    try:
        fmt = OutputFormat(raw_fmt) if raw_fmt else OutputFormat.TEXT
    except ValueError:
        fmt = OutputFormat.TEXT

    color = _bool_env("VAULTPULL_OUTPUT_COLOR", True)
    if "color" in section:
        color = str(section["color"]).strip().lower() not in ("0", "false", "no")

    quiet = _bool_env("VAULTPULL_OUTPUT_QUIET", False)
    if "quiet" in section:
        quiet = str(section["quiet"]).strip().lower() in ("1", "true", "yes")

    return OutputConfig(format=fmt, color=color, quiet=quiet)
