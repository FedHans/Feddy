"""Base fetcher interface."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

log = logging.getLogger("marketbrief")


class BaseFetcher(ABC):
    """Abstract base class for all data fetchers."""

    @abstractmethod
    def fetch(self, config) -> dict:
        """Fetch data and return as a dict."""
        ...
