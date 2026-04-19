"""Retry logic for transient Vault errors."""

import time
import logging
from typing import Callable, Any, Optional, Type, Tuple

logger = logging.getLogger(__name__)


class RetryConfig:
    def __init__(
        self,
        max_attempts: int = 3,
        backoff_base: float = 1.0,
        backoff_max: float = 30.0,
        retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    ):
        self.max_attempts = max_attempts
        self.backoff_base = backoff_base
        self.backoff_max = backoff_max
        self.retryable_exceptions = retryable_exceptions


def load_retry_config(section: Optional[dict] = None) -> RetryConfig:
    """Load retry config from optional config dict section."""
    s = section or {}
    return RetryConfig(
        max_attempts=int(s.get("max_attempts", 3)),
        backoff_base=float(s.get("backoff_base", 1.0)),
        backoff_max=float(s.get("backoff_max", 30.0)),
    )


def with_retry(fn: Callable[[], Any], config: RetryConfig) -> Any:
    """Execute fn with exponential backoff retry on failure."""
    last_exc: Optional[Exception] = None
    for attempt in range(1, config.max_attempts + 1):
        try:
            return fn()
        except config.retryable_exceptions as exc:
            last_exc = exc
            if attempt == config.max_attempts:
                break
            delay = min(config.backoff_base * (2 ** (attempt - 1)), config.backoff_max)
            logger.warning(
                "Attempt %d/%d failed: %s. Retrying in %.1fs.",
                attempt,
                config.max_attempts,
                exc,
                delay,
            )
            time.sleep(delay)
    raise last_exc
