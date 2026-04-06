"""Feishu / Lark delivery channel.

TODO: Port from feishu_bot.py
"""

from __future__ import annotations

import logging

from marketbrief.core.config import MarketBriefConfig

log = logging.getLogger("marketbrief")


def push_report(cfg: MarketBriefConfig, report_path: str | None = None):
    """Push report to Feishu chat."""
    # TODO: port from feishu_bot.py
    log.warning("Feishu push not yet implemented")
