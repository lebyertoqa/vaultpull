"""Output formatting for vaultpull sync results."""
from __future__ import annotations

import json
from enum import Enum
from typing


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    TABLE = "table"


def _pad(value: str, width: int) -> str:
    return value.ljust(width)


def format_text(
    added: List[str],
    changed: List[str],
    skipped: List[str],
    error: Optional[str] = None,
) -> str:
    lines: List[str] = []
    if added:
        lines.append(f"Added   ({len(added)}): {', '.join(added)}")
    if changed:
        lines.append(f"Changed ({len(changed)}): {', '.join(changed)}")
    if skipped:
        lines.append(f"Skipped ({len(skipped)}): {', '.join(skipped)}")
    if error:
        lines.append(f"Error: {error}")
    if not lines:
        lines.append("No changes.")
    return "\n".join(lines)


def format_json(
    added: List[str],
    changed: List[str],
    skipped: List[str],
    error: Optional[str] = None,
) -> str:
    payload: Dict[str, Any] = {
        "added": added,
        "changed": changed,
        "skipped": skipped,
    }
    if error:
        payload["error"] = error
    return json.dumps(payload, indent=2)


def format_table(
    added: List[str],
    changed: List[str],
    skipped: List[str],
    error: Optional[str] = None,
) -> str:
    rows = (
        [(k, "added") for k in added]
        + [(k, "changed") for k in changed]
        + [(k, "skipped") for k in skipped]
    )
    if not rows:
        return "No changes."
    key_w = max(len(r[0]) for r in rows) + 2
    header = _pad("KEY", key_w) + "STATUS"
    sep = "-" * (key_w + 10)
    lines = [header, sep] + [_pad(k, key_w) + s for k, s in rows]
    if error:
        lines.append(sep)
        lines.append(f"Error: {error}")
    return "\n".join(lines)


def render(
    fmt: OutputFormat,
    added: List[str],
    changed: List[str],
    skipped: List[str],
    error: Optional[str] = None,
) -> str:
    if fmt == OutputFormat.JSON:
        return format_json(added, changed, skipped, error)
    if fmt == OutputFormat.TABLE:
        return format_table(added, changed, skipped, error)
    return format_text(added, changed, skipped, error)
