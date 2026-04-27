"""Attach and filter secrets by arbitrary key=value labels."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


def _split_csv(value: str) -> List[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def _split_pairs(raw: str) -> Dict[str, str]:
    """Parse 'key=value,...' into a dict."""
    result: Dict[str, str] = {}
    for token in _split_csv(raw):
        if "=" in token:
            k, _, v = token.partition("=")
            result[k.strip()] = v.strip()
    return result


@dataclass
class LabelConfig:
    labels: Dict[str, str] = field(default_factory=dict)   # labels to attach
    require: Dict[str, str] = field(default_factory=dict)  # labels secrets must have
    environment: str = "default"


def load_label_config(
    section: Optional[Dict[str, str]] = None,
) -> LabelConfig:
    """Load label configuration from an optional config-file section."""
    import os

    sec = section or {}

    raw_labels = sec.get("labels") or os.environ.get("VAULTPULL_LABELS", "")
    raw_require = sec.get("require") or os.environ.get("VAULTPULL_LABEL_REQUIRE", "")
    environment = (
        sec.get("environment")
        or os.environ.get("VAULTPULL_ENVIRONMENT", "default")
    )

    return LabelConfig(
        labels=_split_pairs(raw_labels),
        require=_split_pairs(raw_require),
        environment=environment,
    )


def apply_labels(
    secrets: Dict[str, str],
    cfg: LabelConfig,
    secret_labels: Optional[Dict[str, Dict[str, str]]] = None,
) -> Dict[str, str]:
    """Return only secrets whose labels satisfy *cfg.require*.

    *secret_labels* maps secret key -> {label_key: label_value}.
    If a secret has no entry in *secret_labels* it is treated as having the
    global *cfg.labels* attached to it.
    """
    if not cfg.require:
        return dict(secrets)

    kept: Dict[str, str] = {}
    for key, value in secrets.items():
        effective = dict(cfg.labels)
        if secret_labels:
            effective.update(secret_labels.get(key, {}))
        if all(effective.get(rk) == rv for rk, rv in cfg.require.items()):
            kept[key] = value
    return kept
