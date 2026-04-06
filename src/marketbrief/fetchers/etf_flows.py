"""ETF flow data fetcher — SoSoValue API."""

from __future__ import annotations

import logging

import requests

from marketbrief.core.config import MarketBriefConfig
from marketbrief.utils.retry import retry

log = logging.getLogger("marketbrief")

_SOSOVALUE_BASE = "https://openapi.sosovalue.com/api/v1/etf"

# Endpoint slugs for each asset type
_ETF_ENDPOINTS: dict[str, str] = {
    "BTC": "us-btc-spot",
    "ETH": "us-eth-spot",
}


def _fetch_etf_asset(api_key: str, asset: str, slug: str) -> dict | None:
    """Fetch ETF data for a single asset type from SoSoValue.

    Returns dict with total_aum, daily_flow, funds list, or None on failure.
    """
    url = f"{_SOSOVALUE_BASE}/{slug}"
    log.info("SoSoValue: fetching %s ETF data from %s", asset, url)

    resp = requests.get(
        url,
        headers={
            "x-soso-api-key": api_key,
            "Accept": "application/json",
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    # SoSoValue API response structure: {code, msg, data: {...}}
    if data.get("code") != 0 and data.get("code") != "0":
        # Some APIs use string codes
        code = data.get("code")
        msg = data.get("msg", "unknown error")
        log.warning("SoSoValue %s: API error code=%s msg=%s", asset, code, msg)
        return None

    payload = data.get("data")
    if not payload:
        log.warning("SoSoValue %s: empty data payload", asset)
        return None

    # Extract summary fields
    total_aum = payload.get("totalNetAsset") or payload.get("totalAum") or 0
    daily_flow = payload.get("totalDailyNetflow") or payload.get("dailyFlow") or 0

    # Extract per-fund details if available
    funds_raw = payload.get("list") or payload.get("funds") or []
    funds: list[dict] = []
    for f in funds_raw:
        fund = {
            "name": f.get("name") or f.get("fundName", ""),
            "ticker": f.get("ticker") or f.get("symbol", ""),
            "aum": f.get("netAsset") or f.get("aum") or 0,
            "daily_flow": f.get("dailyNetflow") or f.get("dailyFlow") or 0,
        }
        if fund["name"]:
            funds.append(fund)

    # Convert to billions/millions for readability
    result = {
        "total_aum": total_aum,
        "daily_flow": daily_flow,
        "funds": funds,
        "date": payload.get("date") or payload.get("updateDate", ""),
    }

    log.info("SoSoValue %s: AUM=%.2f, daily_flow=%.2f, %d funds",
             asset, total_aum, daily_flow, len(funds))
    return result


def fetch_etf_flows(cfg: MarketBriefConfig) -> dict:
    """Fetch ETF AUM and flow data from SoSoValue.

    Returns dict: {BTC: {total_aum, daily_flow, funds: [...]}, ETH: {...}}
    Returns empty dict if no API key configured.

    SoSoValue is highest priority for ETF data — retries aggressively.
    """
    if not cfg.sosovalue_api_key:
        log.info("No SoSoValue API key configured — skipping ETF flows fetch")
        return {}

    api_key = cfg.sosovalue_api_key
    etf_config = cfg.dashboard.etf_flows
    results: dict[str, dict] = {}

    # Determine which assets to fetch based on config
    assets_to_fetch: list[tuple[str, str]] = []
    if etf_config.btc_etf and "BTC" in _ETF_ENDPOINTS:
        assets_to_fetch.append(("BTC", _ETF_ENDPOINTS["BTC"]))
    if etf_config.eth_etf and "ETH" in _ETF_ENDPOINTS:
        assets_to_fetch.append(("ETH", _ETF_ENDPOINTS["ETH"]))

    for asset, slug in assets_to_fetch:
        data = retry(
            lambda a=asset, s=slug: _fetch_etf_asset(api_key, a, s),
            max_attempts=3,
            delay=2.0,
            label=f"SoSoValue/{asset}",
        )
        if data and isinstance(data, dict):
            results[asset] = data
        else:
            log.error("SoSoValue %s: all retries exhausted — no data", asset)

    log.info("ETF flows: fetched %d/%d assets", len(results), len(assets_to_fetch))
    return results
