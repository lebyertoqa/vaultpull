"""Merge incoming Vault secrets into an existing .env file,
preserving local-only keys and respecting a conflict strategy."""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Tuple


class MergeStrategy(str, Enum):
    OVERWRITE = "overwrite"   # Vault always wins
    PRESERVE = "preserve"     # local value kept if key already exists
    PROMPT = "prompt"         # caller must resolve conflicts externally


class MergeResult:
    def __init__(
        self,
        merged: Dict[str, str],
        added: List[str],
        updated: List[str],
        preserved: List[str],
        conflicts: List[Tuple[str, str, str]],  # (key, local_val, vault_val)
    ) -> None:
        self.merged = merged
        self.added = added
        self.updated = updated
        self.preserved = preserved
        self.conflicts = conflicts  # non-empty only when strategy == PROMPT

    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)


def merge_secrets(
    local: Dict[str, str],
    incoming: Dict[str, str],
    strategy: MergeStrategy = MergeStrategy.OVERWRITE,
) -> MergeResult:
    """Merge *incoming* (from Vault) into *local* (.env on disk).

    Returns a :class:`MergeResult` describing what changed.
    """
    merged: Dict[str, str] = dict(local)
    added: List[str] = []
    updated: List[str] = []
    preserved: List[str] = []
    conflicts: List[Tuple[str, str, str]] = []

    for key, vault_val in incoming.items():
        if key not in local:
            merged[key] = vault_val
            added.append(key)
        elif local[key] == vault_val:
            pass  # identical — nothing to do
        else:
            if strategy == MergeStrategy.OVERWRITE:
                merged[key] = vault_val
                updated.append(key)
            elif strategy == MergeStrategy.PRESERVE:
                preserved.append(key)
            else:  # PROMPT
                conflicts.append((key, local[key], vault_val))

    return MergeResult(
        merged=merged,
        added=added,
        updated=updated,
        preserved=preserved,
        conflicts=conflicts,
    )


def load_merge_strategy(raw: str | None) -> MergeStrategy:
    """Parse a strategy string, defaulting to OVERWRITE."""
    if raw is None:
        return MergeStrategy.OVERWRITE
    try:
        return MergeStrategy(raw.lower())
    except ValueError:
        raise ValueError(
            f"Unknown merge strategy '{raw}'. "
            f"Valid options: {[s.value for s in MergeStrategy]}"
        )
