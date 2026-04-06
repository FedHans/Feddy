"""Stdout delivery channel — prints report to terminal."""

from __future__ import annotations

import json
import logging

log = logging.getLogger("marketbrief")


def push_report(result: dict):
    """Print report to stdout."""
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
