import json
import time
import pytest
from pathlib import Path
from vaultpull.cache import load_cache, save_cache, invalidate_cache, clear_cache


@pytest.fixture
def cache_dir(tmp_path):
    return str(tmp_path / "cache")


def test_load_cache_miss(cache_dir):
    assert load_cache("secret/app", cache_dir=cache_dir) is None


def test_save_and_load_cache(cache_dir):
    secrets = {"DB_PASS": "hunter2", "API_KEY": "abc123"}
    save_cache("secret/app", secrets, cache_dir=cache_dir)
    result = load_cache("secret/app", cache_dir=cache_dir, ttl=60)
    assert result == secrets


def test_load_cache_expired(cache_dir):
    secrets = {"TOKEN": "xyz"}
    save_cache("secret/app", secrets, cache_dir=cache_dir)
    # backdate the timestamp
    cp = Path(cache_dir) / "secret__app.json"
    data = json.loads(cp.read_text())
    data["ts"] = time.time() - 400
    cp.write_text(json.dumps(data))
    assert load_cache("secret/app", cache_dir=cache_dir, ttl=300) is None
    assert not cp.exists()


def test_load_cache_corrupt_file(cache_dir):
    Path(cache_dir).mkdir(parents=True)
    cp = Path(cache_dir) / "secret__app.json"
    cp.write_text("not json")
    assert load_cache("secret/app", cache_dir=cache_dir) is None


def test_invalidate_existing(cache_dir):
    save_cache("secret/app", {"K": "V"}, cache_dir=cache_dir)
    assert invalidate_cache("secret/app", cache_dir=cache_dir) is True
    assert load_cache("secret/app", cache_dir=cache_dir) is None


def test_invalidate_missing(cache_dir):
    assert invalidate_cache("secret/missing", cache_dir=cache_dir) is False


def test_clear_cache(cache_dir):
    save_cache("secret/a", {"A": "1"}, cache_dir=cache_dir)
    save_cache("secret/b", {"B": "2"}, cache_dir=cache_dir)
    removed = clear_cache(cache_dir=cache_dir)
    assert removed == 2
    assert load_cache("secret/a", cache_dir=cache_dir) is None


def test_clear_cache_empty_dir(cache_dir):
    assert clear_cache(cache_dir=cache_dir) == 0


def test_cache_nested_path(cache_dir):
    secrets = {"X": "y"}
    save_cache("secret/team/app", secrets, cache_dir=cache_dir)
    assert load_cache("secret/team/app", cache_dir=cache_dir, ttl=60) == secrets
