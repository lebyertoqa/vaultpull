"""Audit log support for vaultpull — records sync operations to a local log file."""

import json
import os
from datetime import datetime, timezone
from typing import List, Optional

DEFAULT_AUDIT_LOG = os.path.expanduser("~/.vaultpull_audit.log")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_sync(
    vault_path: str,
    env_file: str,
    keys_written: List[str],
    skipped: Optional[List[str]] = None,
    error: Optional[str] = None,
    log_path: str = DEFAULT_AUDIT_LOG,
) -> None:
    """Append a single sync event to the audit log as a JSON line."""
    entry = {
        "timestamp": _now_iso(),
        "vault_path": vault_path,
        "env_file": env_file,
        "keys_written": keys_written,
        "keys_skipped": skipped or [],
        "error": error,
    }
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def read_log(log_path: str = DEFAULT_AUDIT_LOG) -> List[dict]:
    """Return all audit log entries as a list of dicts."""
    if not os.path.exists(log_path):
        return []
    entries = []
    with open(log_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


def last_sync(log_path: str = DEFAULT_AUDIT_LOG) -> Optional[dict]:
    """Return the most recent audit log entry, or None if log is empty."""
    entries = read_log(log_path)
    return entries[-1] if entries else None
