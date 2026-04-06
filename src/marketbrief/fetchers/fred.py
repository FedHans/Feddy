"""FRED economic data fetcher."""

from __future__ import annotations

import logging
from datetime import date, timedelta

import requests

from marketbrief.core.config import MarketBriefConfig
from marketbrief.utils.retry import retry

log = logging.getLogger("marketbrief")

_FRED_BASE = "https://api.stlouisfed.org/fred"

# Key FRED series: label → series_id
_KEY_SERIES: dict[str, str] = {
    "CPI": "CPIAUCSL",
    "Core CPI": "CPILFESL",
    "PCE": "PCEPI",
    "Core PCE": "PCEPILFE",
    "Unemployment Rate": "UNRATE",
    "Fed Funds Rate": "FEDFUNDS",
    "10Y Yield": "DGS10",
    "2Y Yield": "DGS2",
    "Initial Jobless Claims": "ICSA",
}

# Release name keywords for calendar filtering
_CALENDAR_KEYWORDS: list[str] = [
    "consumer price",
    "cpi",
    "producer price",
    "ppi",
    "gdp",
    "gross domestic",
    "employment",
    "nonfarm",
    "payroll",
    "unemployment",
    "jobless",
    "fomc",
    "federal open market",
    "fed funds",
    "pce",
    "personal consumption",
    "retail sales",
    "housing starts",
    "industrial production",
    "durable goods",
    "ism manufacturing",
    "ism services",
    "trade balance",
    "beige book",
]


def _fetch_series_latest(api_key: str, series_id: str) -> dict | None:
    """Fetch the most recent observation for a single FRED series."""
    url = f"{_FRED_BASE}/series/observations"
    resp = requests.get(
        url,
        params={
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 1,
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    observations = data.get("observations", [])
    if not observations:
        return None

    obs = observations[0]
    value_str = obs.get("value", "")
    # FRED uses "." for missing values
    if value_str in (".", ""):
        return None

    try:
        value = float(value_str)
    except (ValueError, TypeError):
        return None

    return {
        "value": value,
        "date": obs.get("date", ""),
        "series_id": series_id,
    }


def fetch_fred_latest(cfg: MarketBriefConfig) -> dict:
    """Fetch latest values for key FRED series.

    Returns dict mapping label -> {value, date, series_id}.
    Returns empty dict if no FRED API key configured.
    """
    if not cfg.fred_api_key:
        log.info("No FRED API key configured — skipping FRED fetch")
        return {}

    api_key = cfg.fred_api_key
    results: dict[str, dict] = {}

    for label, series_id in _KEY_SERIES.items():
        try:
            obs = retry(
                lambda sid=series_id: _fetch_series_latest(api_key, sid),
                max_attempts=2,
                delay=1.5,
                label=f"FRED/{series_id}",
            )
            if obs:
                results[label] = obs
            else:
                log.warning("FRED: no data for %s (%s)", label, series_id)
        except Exception as e:
            log.warning("FRED: failed to fetch %s (%s): %s", label, series_id, e)

    log.info("FRED: fetched %d/%d series", len(results), len(_KEY_SERIES))
    return results


def fetch_fred_calendar(cfg: MarketBriefConfig, days_ahead: int = 14) -> list[dict]:
    """Fetch upcoming FRED release dates for key economic indicators.

    Uses /fred/releases/dates endpoint filtered by keyword matching.
    Returns list of dicts: [{date, name, release_id, source}]
    Returns empty list if no FRED API key configured.
    """
    if not cfg.fred_api_key:
        log.info("No FRED API key configured — skipping FRED calendar")
        return []

    api_key = cfg.fred_api_key
    today = date.today()
    end_date = today + timedelta(days=days_ahead)

    def _do_fetch() -> list[dict]:
        url = f"{_FRED_BASE}/releases/dates"
        log.info("FRED calendar: fetching releases %s to %s", today.isoformat(), end_date.isoformat())

        all_releases: list[dict] = []
        offset = 0
        limit = 100

        while True:
            resp = requests.get(
                url,
                params={
                    "api_key": api_key,
                    "file_type": "json",
                    "realtime_start": today.isoformat(),
                    "realtime_end": end_date.isoformat(),
                    "include_release_dates_with_no_data": "true",
                    "limit": limit,
                    "offset": offset,
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            dates = data.get("release_dates", [])
            if not dates:
                break

            all_releases.extend(dates)

            if len(dates) < limit:
                break
            offset += limit

        # Filter for key releases by keyword matching
        filtered: list[dict] = []
        for rel in all_releases:
            name = rel.get("release_name", "")
            name_lower = name.lower()
            if any(kw in name_lower for kw in _CALENDAR_KEYWORDS):
                filtered.append({
                    "date": rel.get("date", ""),
                    "name": name,
                    "release_id": rel.get("release_id", ""),
                    "source": "fred",
                })

        # Deduplicate by (date, release_id)
        seen: set[tuple[str, int | str]] = set()
        unique: list[dict] = []
        for item in filtered:
            key = (item["date"], item["release_id"])
            if key not in seen:
                seen.add(key)
                unique.append(item)

        unique.sort(key=lambda x: x["date"])
        log.info("FRED calendar: %d relevant releases in next %d days", len(unique), days_ahead)
        return unique

    result = retry(_do_fetch, max_attempts=2, delay=2.0, label="FRED calendar")
    return result if isinstance(result, list) else []
