"""Economic calendar fetcher — Forex Factory + MyFXBook + FRED.

TODO: Port from morning_fetchers.py fetch_economic_calendar()
"""

from __future__ import annotations

import logging

from marketbrief.core.config import MarketBriefConfig

log = logging.getLogger("marketbrief")


def fetch_calendar(cfg: MarketBriefConfig) -> list[dict]:
    """Fetch economic calendar events.

    Returns list of calendar event dicts.
    """
    # TODO: port from morning_fetchers.py
    log.warning("calendar fetcher not yet implemented — returning stub")
    return []
