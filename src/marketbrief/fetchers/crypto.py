"""Crypto price fetcher — CoinGecko API.

TODO: Port from morning_fetchers.py
"""

from __future__ import annotations

import logging

from marketbrief.core.config import MarketBriefConfig

log = logging.getLogger("marketbrief")


def fetch_crypto(cfg: MarketBriefConfig) -> list[dict]:
    """Fetch crypto prices from CoinGecko.

    Returns list of crypto price dicts.
    """
    # TODO: port from morning_fetchers.py
    log.warning("crypto fetcher not yet implemented — returning stub")
    return []
