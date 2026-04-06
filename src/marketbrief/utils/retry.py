"""Retry utility for flaky external API calls."""

import logging
import time

log = logging.getLogger("marketbrief")


def retry(fn, max_attempts: int = 3, delay: float = 2.0, label: str | None = None):
    """Retry a callable on exception (not empty results).
    Empty results are legitimate (e.g. weekend/market closed)."""
    tag = label or getattr(fn, "__name__", "call")
    last_err = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except Exception as e:
            last_err = e
            if attempt < max_attempts:
                wait = delay * attempt
                log.warning(f"{tag}: attempt {attempt} failed ({e}), retrying in {wait:.0f}s")
                time.sleep(wait)
            else:
                log.error(f"{tag}: all {max_attempts} attempts failed ({e})")
    return {}
