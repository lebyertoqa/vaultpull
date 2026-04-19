"""Utilities for comparing existing .env file contents with fetched secrets."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


_KEY_RE = re.compile(r'^([A-Z_][A-Z0-9_]*)\s*=', re.MULTILINE)
_LINE_RE = re.compile(r'^([A-Z_][A-Z0-9_]*)\s*=\s*(.*)$')


@dataclass
class DiffResult:
    added: List[str] = field(default_factory=list)
    changed: List[str] = field(default_factory=list)
    unchanged: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.changed or self.removed)


def _parse_env_file(path: str) -> Dict[str, str]:
    """Parse a .env file into a key->value dict. Ignores comments and blanks."""
    result: Dict[str, str] = {}
    if not os.path.exists(path):
        return result
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = _LINE_RE.match(line)
            if m:
                result[m.group(1)] = m.group(2).strip('"').strip("'")
    return result


def compute_diff(env_path: str, incoming: Dict[str, str]) -> DiffResult:
    """Compare incoming secrets dict against the existing .env file.

    Args:
        env_path: Path to the existing .env file (may not exist).
        incoming: Dict of key->value secrets fetched from Vault.

    Returns:
        DiffResult describing what would change.
    """
    existing = _parse_env_file(env_path)
    result = DiffResult()

    for key, value in incoming.items():
        if key not in existing:
            result.added.append(key)
        elif existing[key] != value:
            result.changed.append(key)
        else:
            result.unchanged.append(key)

    for key in existing:
        if key not in incoming:
            result.removed.append(key)

    return result
