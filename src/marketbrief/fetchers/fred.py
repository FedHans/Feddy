"""FRED economic data fetcher.

TODO: Port from morning_fetchers.py fetch_fred_latest() + fetch_fred_calendar()
"""

from __future__ import annotations

import logging

from marketbrief.core.config import MarketBriefConfig

log = logging.getLogger("marketbrief")


def fetch_fred_latest(cfg: MarketBriefConfig) -> dict:
    """Fetch latest values for key FRED series.

    Returns dict mapping label → {value, date, series_id}.
    """
    # TODO: port from morning_fetchers.py
    log.warning("FRED fetcher not yet implemented — returning stub")
    return {}
