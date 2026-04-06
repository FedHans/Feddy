"""Base delivery channel interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseChannel(ABC):
    """Abstract base class for delivery channels."""

    @abstractmethod
    def send(self, messages: list[str], attachments: list[str] | None = None):
        """Send messages (and optional file attachments) to the channel."""
        ...
