"""Economic calendar fetcher — Forex Factory + MyFXBook."""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

from marketbrief.core.config import MarketBriefConfig
from marketbrief.utils.retry import retry

log = logging.getLogger("marketbrief")

_ET_TZ = ZoneInfo("America/New_York")
_UTC_TZ = timezone.utc

# MyFXBook country → currency code mapping
_COUNTRY_TO_CCY: dict[str, str] = {
    "United States": "USD",
    "European Monetary Union": "EUR",
    "Euro Zone": "EUR",
    "Eurozone": "EUR",
    "Germany": "EUR",
    "France": "EUR",
    "Italy": "EUR",
    "Spain": "EUR",
    "United Kingdom": "GBP",
    "Japan": "JPY",
    "China": "CNY",
    "Canada": "CAD",
    "Australia": "AUD",
    "New Zealand": "NZD",
    "Switzerland": "CHF",
    "Sweden": "SEK",
    "Norway": "NOK",
    "South Korea": "KRW",
    "India": "INR",
    "Brazil": "BRL",
    "Mexico": "MXN",
    "Singapore": "SGD",
    "Hong Kong": "HKD",
    "Turkey": "TRY",
    "South Africa": "ZAR",
}

# Impact mapping for Forex Factory
_FF_IMPACT: dict[str, str] = {
    "High": "high",
    "Medium": "medium",
    "Low": "low",
    "Holiday": "low",
    "Non-Economic": "low",
}


def _normalize_event_name(name: str) -> str:
    """Normalize event name for deduplication: lowercase, strip whitespace/punctuation variants."""
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9\s]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name


def _fetch_ff_calendar(target_date: date) -> list[dict]:
    """Fetch economic calendar events from Forex Factory JSON feed.

    Returns list of event dicts for the target_date.
    """
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    log.info("FF calendar: fetching %s", url)

    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    events: list[dict] = []
    target_str = target_date.isoformat()  # "YYYY-MM-DD"

    for item in data:
        # Date field is like "2026-04-06T08:30:00-04:00" or "2026-04-06"
        raw_date = item.get("date", "")
        if not raw_date:
            continue

        # Check if event falls on target_date
        try:
            if "T" in raw_date:
                dt = datetime.fromisoformat(raw_date)
                event_date = dt.date()
            else:
                event_date = date.fromisoformat(raw_date[:10])
        except (ValueError, TypeError):
            continue

        if event_date != target_date:
            continue

        # Extract time
        time_str = ""
        if "T" in raw_date:
            try:
                dt = datetime.fromisoformat(raw_date)
                # Convert to ET
                dt_et = dt.astimezone(_ET_TZ)
                time_str = dt_et.strftime("%H:%M ET")
            except Exception:
                pass

        title = item.get("title", "").strip()
        if not title:
            continue

        country = item.get("country", "")
        impact_raw = item.get("impact", "Low")
        impact = _FF_IMPACT.get(impact_raw, "medium")
        forecast = item.get("forecast", "")
        previous = item.get("previous", "")

        event = {
            "time": time_str or "All Day",
            "name": title,
            "impact": impact,
            "country": country,
            "forecast": forecast if forecast else "",
            "previous": previous if previous else "",
            "source": "ff",
        }
        events.append(event)

    log.info("FF calendar: %d events for %s", len(events), target_str)
    return events


def _fetch_myfxbook_calendar(target_date: date) -> list[dict]:
    """Fetch economic calendar events from MyFXBook RSS feed.

    Returns list of event dicts for the target_date.
    """
    url = "https://www.myfxbook.com/rss/forex-economic-calendar-events"
    log.info("MyFXBook calendar: fetching %s", url)

    resp = requests.get(url, timeout=15, headers={"User-Agent": "MarketBrief/1.0"})
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    events: list[dict] = []
    target_str = target_date.isoformat()

    for item in root.iter("item"):
        title_el = item.find("title")
        desc_el = item.find("description")
        pub_el = item.find("pubDate")

        if title_el is None or pub_el is None:
            continue

        # Parse pubDate — RFC 822 format: "Mon, 06 Apr 2026 12:30:00 GMT"
        pub_str = (pub_el.text or "").strip()
        try:
            dt_utc = datetime.strptime(pub_str, "%a, %d %b %Y %H:%M:%S %Z")
            dt_utc = dt_utc.replace(tzinfo=_UTC_TZ)
        except (ValueError, TypeError):
            # Try alternative format
            try:
                dt_utc = datetime.strptime(pub_str, "%a, %d %b %Y %H:%M:%S %z")
            except (ValueError, TypeError):
                continue

        # Convert GMT → ET
        dt_et = dt_utc.astimezone(_ET_TZ)
        event_date = dt_et.date()

        if event_date != target_date:
            continue

        time_str = dt_et.strftime("%H:%M ET")

        raw_title = (title_el.text or "").strip()
        description = (desc_el.text or "").strip() if desc_el is not None else ""

        # Parse country/impact from title or description
        # MyFXBook title format: "Country - Event Name"
        country_code = ""
        event_name = raw_title
        if " - " in raw_title:
            parts = raw_title.split(" - ", 1)
            country_name = parts[0].strip()
            event_name = parts[1].strip()
            country_code = _COUNTRY_TO_CCY.get(country_name, country_name[:3].upper())

        # Try to extract impact from description
        impact = "medium"
        desc_lower = description.lower()
        if "high" in desc_lower:
            impact = "high"
        elif "low" in desc_lower:
            impact = "low"

        # Extract forecast/previous from description if present
        forecast = ""
        previous = ""
        forecast_match = re.search(r"Forecast:\s*([^\s,;]+)", description)
        previous_match = re.search(r"Previous:\s*([^\s,;]+)", description)
        if forecast_match:
            forecast = forecast_match.group(1)
        if previous_match:
            previous = previous_match.group(1)

        event = {
            "time": time_str,
            "name": event_name,
            "impact": impact,
            "country": country_code,
            "forecast": forecast,
            "previous": previous,
            "source": "myfxbook",
        }
        events.append(event)

    log.info("MyFXBook calendar: %d events for %s", len(events), target_str)
    return events


def fetch_calendar(cfg: MarketBriefConfig) -> list[dict]:
    """Fetch economic calendar events from multiple sources, merged and deduplicated.

    Returns list of calendar event dicts for today.
    """
    today = date.today()

    # Fetch from both sources with retry
    ff_events: list[dict] = retry(
        lambda: _fetch_ff_calendar(today),
        max_attempts=2,
        delay=2.0,
        label="FF calendar",
    ) or []

    myfxbook_events: list[dict] = retry(
        lambda: _fetch_myfxbook_calendar(today),
        max_attempts=2,
        delay=2.0,
        label="MyFXBook calendar",
    ) or []

    # Merge: start with FF (primary), add non-duplicate MyFXBook events
    seen_names: set[str] = set()
    merged: list[dict] = []

    for ev in ff_events:
        norm = _normalize_event_name(ev["name"])
        seen_names.add(norm)
        merged.append(ev)

    for ev in myfxbook_events:
        norm = _normalize_event_name(ev["name"])
        if norm not in seen_names:
            seen_names.add(norm)
            merged.append(ev)

    # Sort by time: events with specific times first, then "All Day"
    def _sort_key(ev: dict) -> tuple[int, str]:
        t = ev.get("time", "")
        if t and ":" in t and t != "All Day":
            return (0, t)
        return (1, t)

    merged.sort(key=_sort_key)

    log.info("Calendar: %d merged events (FF=%d, MyFXBook=%d)",
             len(merged), len(ff_events), len(myfxbook_events))
    return merged
