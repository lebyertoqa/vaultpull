"""Tag-based filtering and labeling for Vault secrets."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TagConfig:
    required_tags: List[str] = field(default_factory=list)
    excluded_tags: List[str] = field(default_factory=list)
    tag_prefix: str = "tag:"
    strict: bool = False  # if True, secrets with no tags are excluded


def _split_csv(value: str) -> List[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def load_tag_config(section: Optional[Dict] = None) -> TagConfig:
    """Load TagConfig from an optional config dict section."""
    section = section or {}
    return TagConfig(
        required_tags=_split_csv(section.get("required_tags", "")),
        excluded_tags=_split_csv(section.get("excluded_tags", "")),
        tag_prefix=section.get("tag_prefix", "tag:"),
        strict=str(section.get("strict", "false")).lower() == "true",
    )


def extract_tags(secret: Dict, tag_prefix: str = "tag:") -> List[str]:
    """Extract tag values from a secret dict by scanning keys with the tag prefix."""
    return [
        key[len(tag_prefix):]
        for key in secret
        if key.startswith(tag_prefix)
    ]


def secret_matches_tags(secret: Dict, cfg: TagConfig) -> bool:
    """Return True if the secret satisfies required/excluded tag constraints."""
    tags = extract_tags(secret, cfg.tag_prefix)

    if cfg.strict and not tags:
        return False

    for req in cfg.required_tags:
        if req not in tags:
            return False

    for exc in cfg.excluded_tags:
        if exc in tags:
            return False

    return True


def apply_tag_filter(
    secrets: Dict[str, Dict], cfg: TagConfig
) -> Dict[str, Dict]:
    """Filter a mapping of {key: secret_dict} by tag constraints."""
    return {
        k: v
        for k, v in secrets.items()
        if secret_matches_tags(v, cfg)
    }


def group_secrets_by_tag(
    secrets: Dict[str, Dict], cfg: TagConfig
) -> Dict[str, List[str]]:
    """Group secret keys by their tags.

    Returns a dict mapping each tag value to the list of secret keys that
    carry that tag.  Secrets not matching the tag filter are excluded.
    """
    groups: Dict[str, List[str]] = {}
    for key, secret in secrets.items():
        if not secret_matches_tags(secret, cfg):
            continue
        for tag in extract_tags(secret, cfg.tag_prefix):
            groups.setdefault(tag, []).append(key)
    return groups
