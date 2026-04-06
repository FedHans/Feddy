"""News fetcher — RSS feeds + SoSoValue news.

TODO: Port from morning_fetchers.py fetch_morning_news() + fetch_rss_feed()
"""

from __future__ import annotations

import logging

from marketbrief.core.config import MarketBriefConfig

log = logging.getLogger("marketbrief")


def fetch_news(cfg: MarketBriefConfig) -> list[dict]:
    """Fetch news from all configured RSS feeds.

    Returns list of news item dicts.
    """
    # TODO: port from morning_fetchers.py
    log.warning("news fetcher not yet implemented — returning stub")
    return []
