"""Timezone conversion utilities."""

import datetime
import re


def et_to_beijing(time_str: str) -> str:
    """Convert 'HH:MM ET' to dual-display string with UTC+8.
    Returns: '08:30 ET (20:30 UTC+8)' or original string if no match."""
    from zoneinfo import ZoneInfo

    et_tz = ZoneInfo("America/New_York")
    bj_tz = ZoneInfo("Asia/Shanghai")
    today = datetime.date.today()

    def _convert_match(m):
        h, mi = int(m.group(1)), int(m.group(2))
        try:
            et_dt = datetime.datetime(today.year, today.month, today.day, h, mi, tzinfo=et_tz)
            bj_dt = et_dt.astimezone(bj_tz)
            return f'{m.group(0)} ({bj_dt.strftime("%H:%M")} UTC+8)'
        except Exception:
            return m.group(0)

    return re.sub(r'(\d{1,2}):(\d{2})\s*ET\b', _convert_match, time_str)


def et_time_field_to_beijing(time_field: str) -> str:
    """Convert a calendar 'time' field like '08:30 ET' to dual display.
    Handles 'Ongoing', 'Pre-market', etc. gracefully."""
    if not time_field or "ET" not in time_field:
        return time_field
    return et_to_beijing(time_field)
