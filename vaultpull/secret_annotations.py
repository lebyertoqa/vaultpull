"""Secret annotations: attach arbitrary metadata key-value pairs to secrets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


def _split_pairs(raw: str) -> Dict[str, str]:
    """Parse 'key=value,...' into a dict, skipping malformed tokens."""
    result: Dict[str, str] = {}
    for token in raw.split(","):
        token = token.strip()
        if "=" in token:
            k, _, v = token.partition("=")
            k, v = k.strip(), v.strip()
            if k:
                result[k] = v
    return result


@dataclass
class AnnotationConfig:
    """Configuration for secret annotations."""
    annotations: Dict[str, str] = field(default_factory=dict)  # global annotations
    per_key: Dict[str, Dict[str, str]] = field(default_factory=dict)  # key -> {meta}
    environment: str = "default"


def load_annotation_config(
    section: Optional[Dict] = None,
    environment: str = "default",
) -> AnnotationConfig:
    """Build an AnnotationConfig from an optional config dict section."""
    import os

    section = section or {}

    raw_global = section.get("annotations") or os.environ.get("VAULTPULL_ANNOTATIONS", "")
    global_annotations = _split_pairs(raw_global) if raw_global else {}

    per_key: Dict[str, Dict[str, str]] = {}
    for k, v in section.items():
        if k.startswith("annotate.") and isinstance(v, str):
            secret_key = k[len("annotate."):]
            per_key[secret_key] = _split_pairs(v)

    return AnnotationConfig(
        annotations=global_annotations,
        per_key=per_key,
        environment=environment,
    )


def annotate_secrets(
    secrets: Dict[str, str],
    cfg: AnnotationConfig,
) -> Dict[str, Dict]:
    """Return a mapping of secret key -> {value, annotations}."""
    result: Dict[str, Dict] = {}
    for key, value in secrets.items():
        merged = dict(cfg.annotations)
        merged.update(cfg.per_key.get(key, {}))
        result[key] = {"value": value, "annotations": merged}
    return result


@dataclass
class AnnotationReport:
    environment: str
    total: int
    annotated: int
    annotation_keys: List[str]


def build_annotation_report(
    secrets: Dict[str, str],
    cfg: AnnotationConfig,
) -> AnnotationReport:
    annotated_data = annotate_secrets(secrets, cfg)
    annotated_count = sum(
        1 for v in annotated_data.values() if v["annotations"]
    )
    all_keys: List[str] = sorted(
        {k for v in annotated_data.values() for k in v["annotations"]}
    )
    return AnnotationReport(
        environment=cfg.environment,
        total=len(secrets),
        annotated=annotated_count,
        annotation_keys=all_keys,
    )


def format_annotation_report(report: AnnotationReport) -> str:
    lines = [
        f"Annotation Report [{report.environment}]",
        f"  Total secrets : {report.total}",
        f"  Annotated     : {report.annotated}",
        f"  Annotation keys: {', '.join(report.annotation_keys) or '(none)'}",
    ]
    return "\n".join(lines)
