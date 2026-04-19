"""Sync notification hooks for vaultpull."""

import json
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Optional


@dataclass
class NotifyConfig:
    webhook_url: Optional[str] = None
    on_success: bool = True
    on_failure: bool = True
    on_no_changes: bool = False


def _build_payload(status: str, path: str, added: int, changed: int, removed: int, error: Optional[str] = None) -> dict:
    payload = {
        "tool": "vaultpull",
        "status": status,
        "env_file": path,
        "changes": {"added": added, "changed": changed, "removed": removed},
    }
    if error:
        payload["error"] = error
    return payload


def send_webhook(config: NotifyConfig, payload: dict) -> bool:
    """POST payload as JSON to the configured webhook URL. Returns True on success."""
    if not config.webhook_url:
        return False
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        config.webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5):
            return True
    except urllib.error.URLError:
        return False


def notify_sync(
    config: NotifyConfig,
    status: str,
    path: str,
    added: int = 0,
    changed: int = 0,
    removed: int = 0,
    error: Optional[str] = None,
) -> bool:
    """Send a sync notification if the webhook is configured and the event is enabled."""
    if not config.webhook_url:
        return False
    if status == "success" and not config.on_success:
        return False
    if status == "failure" and not config.on_failure:
        return False
    if status == "no_changes" and not config.on_no_changes:
        return False
    payload = _build_payload(status, path, added, changed, removed, error)
    return send_webhook(config, payload)
