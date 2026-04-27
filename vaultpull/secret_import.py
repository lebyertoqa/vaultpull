"""Import secrets from an external .env file into the vault pull pipeline."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_KEY_RE = re.compile(r'^[A-Z_][A-Z0-9_]*$')


@dataclass
class ImportConfig:
    source_file: str = ".env.import"
    prefix: str = ""
    overwrite: bool = False
    skip_invalid: bool = True
    encoding: str = "utf-8"


def load_import_config(section: Optional[Dict] = None) -> ImportConfig:
    """Load ImportConfig from an optional config dict, falling back to env vars."""
    s = section or {}
    return ImportConfig(
        source_file=s.get("source_file") or os.environ.get("VAULTPULL_IMPORT_SOURCE", ".env.import"),
        prefix=s.get("prefix") or os.environ.get("VAULTPULL_IMPORT_PREFIX", ""),
        overwrite=_bool(s.get("overwrite"), os.environ.get("VAULTPULL_IMPORT_OVERWRITE", "false")),
        skip_invalid=_bool(s.get("skip_invalid"), os.environ.get("VAULTPULL_IMPORT_SKIP_INVALID", "true")),
        encoding=s.get("encoding") or os.environ.get("VAULTPULL_IMPORT_ENCODING", "utf-8"),
    )


def _bool(dict_val: Optional[str], env_val: str) -> bool:
    if dict_val is not None:
        return str(dict_val).lower() in ("true", "1", "yes")
    return env_val.lower() in ("true", "1", "yes")


@dataclass
class ImportResult:
    imported: Dict[str, str] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.imported)

    @property
    def ok(self) -> bool:
        """Return True if there were no errors during import."""
        return len(self.errors) == 0


def _parse_env_line(line: str):
    """Parse a single KEY=VALUE line. Returns (key, value) or None."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    if "=" not in line:
        return None
    key, _, value = line.partition("=")
    key = key.strip()
    value = value.strip().strip('"').strip("'")
    return key, value


def import_env_file(
    cfg: ImportConfig,
    existing: Optional[Dict[str, str]] = None,
) -> ImportResult:
    """Read source_file and return an ImportResult with parsed secrets."""
    result = ImportResult()
    existing = existing or {}

    if not os.path.exists(cfg.source_file):
        result.errors.append(f"Source file not found: {cfg.source_file}")
        return result

    try:
        with open(cfg.source_file, encoding=cfg.encoding) as fh:
            lines = fh.readlines()
    except OSError as exc:
        result.errors.append(f"Cannot read {cfg.source_file}: {exc}")
        return result

    for raw in lines:
        parsed = _parse_env_line(raw)
        if parsed is None:
            continue
        key, value = parsed
        full_key = (cfg.prefix + key) if cfg.prefix else key
        if not _KEY_RE.match(full_key):
            if cfg.skip_invalid:
                result.skipped.append(full_key)
            else:
                result.errors.append(f"Invalid key: {full_key!r}")
            continue
        if full_key in existing and not cfg.overwrite:
            result.skipped.append(full_key)
            continue
        result.imported[full_key] = value

    return result
