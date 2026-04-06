"""ETF flow data fetcher — SoSoValue API + RSS fallback.

TODO: Port from morning_fetchers.py
"""

from __future__ import annotations

import logging

from marketbrief.core.config import MarketBriefConfig

log = logging.getLogger("marketbrief")


def fetch_etf_flows(cfg: MarketBriefConfig) -> dict:
    """Fetch ETF AUM and flow data.

    Returns dict with BTC/ETH/Gold ETF data.
    """
    # TODO: port from morning_fetchers.py
    log.warning("ETF flows fetcher not yet implemented — returning stub")
    return {}
