"""Market data fetcher — Yahoo Finance (primary) + Stooq (fallback).

TODO: Port from morning_fetchers.py build_market_snapshot()
"""

from __future__ import annotations

import logging

from marketbrief.core.config import MarketBriefConfig

log = logging.getLogger("marketbrief")


def fetch_market_snapshot(cfg: MarketBriefConfig) -> dict:
    """Fetch current market prices for all dashboard assets.

    Returns dict with 'text' (formatted snapshot for Claude) and raw data.
    """
    # TODO: port from morning_fetchers.py
    log.warning("market fetcher not yet implemented — returning stub")
    return {"text": "MARKET SNAPSHOT: stub — not yet implemented", "prices": {}}
