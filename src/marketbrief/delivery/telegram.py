"""Telegram delivery channel.

TODO: Port from push_daily_report.py
"""

from __future__ import annotations

import logging

from marketbrief.core.config import MarketBriefConfig

log = logging.getLogger("marketbrief")


def push_report(cfg: MarketBriefConfig, report_path: str | None = None):
    """Push report to Telegram chat and channel."""
    # TODO: port from push_daily_report.py
    log.warning("Telegram push not yet implemented")
