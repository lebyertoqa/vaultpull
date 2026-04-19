"""Rollback support: backup and restore .env files before sync."""

import os
import shutil
from datetime import datetime
from pathlib import Path


BACKUP_SUFFIX = ".vaultpull.bak"


def backup_env_file(env_path: str) -> str | None:
    """Copy env_path to a timestamped backup. Returns backup path or None if source missing."""
    src = Path(env_path)
    if not src.exists():
        return None
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    backup_path = src.with_suffix(f".{ts}{BACKUP_SUFFIX}")
    shutil.copy2(src, backup_path)
    return str(backup_path)


def restore_env_file(backup_path: str, env_path: str) -> None:
    """Restore env_path from backup_path. Raises FileNotFoundError if backup missing."""
    src = Path(backup_path)
    if not src.exists():
        raise FileNotFoundError(f"Backup not found: {backup_path}")
    shutil.copy2(src, env_path)


def list_backups(env_path: str) -> list[str]:
    """Return sorted list of backup files for the given env_path."""
    src = Path(env_path)
    parent = src.parent
    pattern = f"{src.stem}.*{BACKUP_SUFFIX}"
    backups = sorted(parent.glob(pattern))
    return [str(p) for p in backups]


def prune_backups(env_path: str, keep: int = 5) -> list[str]:
    """Delete oldest backups, keeping only `keep` most recent. Returns list of deleted paths."""
    backups = list_backups(env_path)
    to_delete = backups[: max(0, len(backups) - keep)]
    for path in to_delete:
        os.remove(path)
    return to_delete
