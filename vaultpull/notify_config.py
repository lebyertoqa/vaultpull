"""Load NotifyConfig from vaultpull config dict or environment variables."""

import os
from vaultpull.notify import NotifyConfig


def _bool_env(key: str, default: bool) -> bool:
    val = os.environ.get(key)
    if val is None:
        return default
    return val.lower() in ("1", "true", "yes")


def load_notify_config(raw: dict) -> NotifyConfig:
    """Build a NotifyConfig from a config dict, falling back to env vars.

    Supported keys under ``notify`` section::

        notify:
          webhook_url: https://...
          on_success: true
          on_failure: true
          on_no_changes: false
    """
    section = raw.get("notify", {})

    webhook_url = (
        section.get("webhook_url")
        or os.environ.get("VAULTPULL_WEBHOOK_URL")
    )

    on_success = section.get("on_success", _bool_env("VAULTPULL_NOTIFY_SUCCESS", True))
    on_failure = section.get("on_failure", _bool_env("VAULTPULL_NOTIFY_FAILURE", True))
    on_no_changes = section.get("on_no_changes", _bool_env("VAULTPULL_NOTIFY_NO_CHANGES", False))

    return NotifyConfig(
        webhook_url=webhook_url or None,
        on_success=bool(on_success),
        on_failure=bool(on_failure),
        on_no_changes=bool(on_no_changes),
    )
