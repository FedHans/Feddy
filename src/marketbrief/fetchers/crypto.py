"""Crypto price fetcher — CoinGecko API."""

from __future__ import annotations

import logging

import requests

from marketbrief.core.config import MarketBriefConfig
from marketbrief.utils.retry import retry

log = logging.getLogger("marketbrief")

_COINGECKO_MARKETS_URL = "https://api.coingecko.com/api/v3/coins/markets"


def fetch_crypto(cfg: MarketBriefConfig) -> list[dict]:
    """Fetch crypto prices from CoinGecko.

    Reads coin IDs from cfg.dashboard.crypto_ids (default: bitcoin, ethereum, solana).
    Returns list of dicts: [{symbol, name, price, chg_24h, chg_7d, mcap_b}]
    """
    ids = cfg.dashboard.crypto_ids
    if not ids:
        log.info("No crypto IDs configured — skipping crypto fetch")
        return []

    ids_str = ",".join(ids)

    def _do_fetch() -> list[dict]:
        log.info("CoinGecko: fetching %d coins (%s)", len(ids), ids_str)
        resp = requests.get(
            _COINGECKO_MARKETS_URL,
            params={
                "vs_currency": "usd",
                "ids": ids_str,
                "order": "market_cap_desc",
                "per_page": 20,
                "page": 1,
                "price_change_percentage": "24h,7d",
            },
            timeout=15,
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()

        results: list[dict] = []
        for coin in data:
            symbol = (coin.get("symbol") or "").upper()
            name = coin.get("name", "")
            price = coin.get("current_price") or 0.0
            chg_24h = coin.get("price_change_percentage_24h_in_currency") or coin.get(
                "price_change_percentage_24h"
            ) or 0.0
            chg_7d = coin.get("price_change_percentage_7d_in_currency") or 0.0
            mcap = coin.get("market_cap") or 0
            mcap_b = round(mcap / 1e9, 2) if mcap else 0.0

            results.append({
                "symbol": symbol,
                "name": name,
                "price": price,
                "chg_24h": round(chg_24h, 2),
                "chg_7d": round(chg_7d, 2),
                "mcap_b": mcap_b,
            })

        log.info("CoinGecko: fetched %d coins", len(results))
        return results

    result = retry(_do_fetch, max_attempts=3, delay=2.0, label="CoinGecko")
    return result if isinstance(result, list) else []
