"""Simple file-based cache for Vault secrets to avoid redundant fetches."""

import json
import os
import time
from pathlib import Path
from typing import Dict, Optional

DEFAULT_CACHE_DIR = ".vaultpull_cache"
DEFAULT_TTL = 300  # seconds


def _cache_path(cache_dir: str, path: str) -> Path:
    safe = path.strip("/").replace("/", "__")
    return Path(cache_dir) / f"{safe}.json"


def load_cache(path: str, cache_dir: str = DEFAULT_CACHE_DIR, ttl: int = DEFAULT_TTL) -> Optional[Dict[str, str]]:
    """Return cached secrets for vault path if present and not expired."""
    cp = _cache_path(cache_dir, path)
    if not cp.exists():
        return None
    try:
        data = json.loads(cp.read_text())
        if time.time() - data["ts"] > ttl:
            cp.unlink(missing_ok=True)
            return None
        return data["secrets"]
    except (KeyError, json.JSONDecodeError, OSError):
        return None


def save_cache(path: str, secrets: Dict[str, str], cache_dir: str = DEFAULT_CACHE_DIR) -> None:
    """Persist secrets for vault path to the cache."""
    cp = _cache_path(cache_dir, path)
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text(json.dumps({"ts": time.time(), "secrets": secrets}))


def invalidate_cache(path: str, cache_dir: str = DEFAULT_CACHE_DIR) -> bool:
    """Remove cached entry for vault path. Returns True if removed."""
    cp = _cache_path(cache_dir, path)
    if cp.exists():
        cp.unlink()
        return True
    return False


def clear_cache(cache_dir: str = DEFAULT_CACHE_DIR) -> int:
    """Remove all cache files. Returns count removed."""
    d = Path(cache_dir)
    if not d.exists():
        return 0
    removed = 0
    for f in d.glob("*.json"):
        f.unlink()
        removed += 1
    return removed
