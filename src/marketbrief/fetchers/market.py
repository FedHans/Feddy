"""Market data fetcher — Yahoo Finance (primary) + Frankfurter FX + Stooq (fallback).

Merge priority per asset class:
  FX pairs:  Frankfurter API (ECB, primary) → YF → Stooq
  Others:    YF (primary) → Stooq (fallback, only for gaps)
"""

from __future__ import annotations

import concurrent.futures
import datetime
import logging
from typing import Any

import requests

from marketbrief.core.config import MarketBriefConfig
from marketbrief.core.types import DashboardConfig
from marketbrief.utils.formatting import dir_emoji, fmt_val, group_fmt
from marketbrief.utils.retry import retry

log = logging.getLogger("marketbrief")

# ── Constants ────────────────────────────────────────────────────────────────

# Frankfurter API uses ECB reference rates with ISO currency codes.
# Keys are standard FX pair labels; values are Frankfurter symbol codes.
FRANKFURTER_FX: dict[str, str] = {
    "EUR/USD": "EUR",
    "USD/JPY": "JPY",
    "GBP/USD": "GBP",
    "USD/CAD": "CAD",
    "AUD/USD": "AUD",
    "USD/CNH": "CNY",  # CNY (onshore) as proxy for CNH (offshore)
}

# Asset groups to iterate when building the snapshot text.
_SNAPSHOT_GROUPS: list[tuple[str, str]] = [
    ("precious_metals", "Precious Metals"),
    ("energy",          "Energy"),
    ("equities",        "US Equities"),
    ("rates",           "US Rates (yield %)"),
    ("volatility",      "Volatility"),
    ("fx",              "FX"),
    ("sectors",         "S&P 500 Sectors"),
]


# ── Public API ───────────────────────────────────────────────────────────────


def fetch_market_snapshot(cfg: MarketBriefConfig) -> dict[str, Any]:
    """Fetch current market prices for all dashboard assets.

    Returns a dict with:
      - ``text``:   formatted snapshot string for Claude prompt injection
      - ``prices``: ``{label: {label, symbol, close, open, high, low, chg_pct, date}}``
      - ``data_sources``: human-readable provenance string
    """
    dashboard = cfg.dashboard

    # Collect all labels and corresponding Stooq symbols for fallback
    all_labels: set[str] = set()
    stooq_tasks: list[tuple[str, str]] = []
    for grp_key in ("precious_metals", "energy", "metals_energy", "equities",
                     "rates", "volatility", "fx", "sectors"):
        for item in getattr(dashboard, grp_key, []):
            if item.label not in all_labels and item.stooq:
                stooq_tasks.append((item.stooq, item.label))
            all_labels.add(item.label)

    # ── Concurrent primary fetches ───────────────────────────────────────
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        yf_future = ex.submit(
            retry, lambda: fetch_yfinance_batch(dashboard), label="Yahoo Finance",
        )
        fx_future = ex.submit(
            retry, lambda: fetch_frankfurter_fx(), label="Frankfurter FX",
        )

        yf_results: dict[str, dict] = yf_future.result()
        fx_results: dict[str, dict] = fx_future.result()

        yf_count = len(yf_results)
        fx_count = len(fx_results)

        # Merge: YF as base, Frankfurter overwrites FX pairs
        market_results: dict[str, dict] = {}
        market_results.update(yf_results)
        market_results.update(fx_results)

        # Stooq fallback — only for labels still missing
        covered = set(market_results.keys())
        missing_labels = all_labels - covered
        stooq_filled = 0

        if missing_labels:
            log.info(
                "Frankfurter(%d) + YF(%d) covered %d/%d; Stooq for %d gaps",
                fx_count, yf_count, len(covered), len(all_labels), len(missing_labels),
            )
            stooq_gap_tasks = [
                (sym, lbl) for sym, lbl in stooq_tasks if lbl in missing_labels
            ]
            stooq_futures = {
                ex.submit(fetch_stooq, sym, lbl): lbl
                for sym, lbl in stooq_gap_tasks
            }
            for fut in concurrent.futures.as_completed(stooq_futures):
                lbl = stooq_futures[fut]
                res = fut.result()
                if res:
                    market_results[lbl] = res
                    stooq_filled += 1
            if stooq_filled:
                log.info("Stooq filled %d/%d gaps", stooq_filled, len(missing_labels))
        else:
            log.info(
                "Frankfurter(%d) + YF(%d) covered all %d labels — Stooq skipped",
                fx_count, yf_count, len(all_labels),
            )

    # ── Build formatted text ─────────────────────────────────────────────
    text = _format_snapshot_text(dashboard, market_results)

    data_sources = (
        f"Frankfurter({fx_count}) · Yahoo Finance({yf_count}) · Stooq({stooq_filled})"
    )

    return {
        "text": text,
        "prices": market_results,
        "data_sources": data_sources,
    }


# ── Yahoo Finance (primary) ─────────────────────────────────────────────────


def fetch_yfinance_batch(dashboard: DashboardConfig) -> dict[str, dict]:
    """Batch-fetch all symbols via Yahoo Finance.

    Returns ``{label: {label, symbol, close, open, high, low, chg_pct, date}}``.
    """
    try:
        import yfinance as yf  # type: ignore[import-untyped]
    except ImportError:
        log.warning("yfinance not installed — skipping Yahoo Finance (primary source)")
        return {}

    # Build label → yf_symbol mapping from dashboard groups
    label_to_yf: dict[str, str] = {}
    for grp_key in ("precious_metals", "energy", "metals_energy", "equities",
                     "rates", "volatility", "fx", "sectors"):
        for item in getattr(dashboard, grp_key, []):
            if item.yf:
                label_to_yf[item.label] = item.yf

    if not label_to_yf:
        return {}

    yf_symbols = list(set(label_to_yf.values()))

    # Download with hard timeout to prevent hanging
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as _yf_ex:
            _yf_fut = _yf_ex.submit(
                yf.download, yf_symbols, period="5d", progress=False, threads=True,
            )
            data = _yf_fut.result(timeout=30)
        if data.empty:
            log.warning("Yahoo Finance returned empty data (market may be closed)")
            return {}
    except concurrent.futures.TimeoutError:
        log.warning("Yahoo Finance timed out (30s) — falling back to Stooq")
        return {}
    except Exception as e:
        log.warning("Yahoo Finance download failed: %s", e)
        return {}

    results: dict[str, dict] = {}
    for label, yf_sym in label_to_yf.items():
        try:
            col = data[("Close", yf_sym)].dropna()
            if len(col) < 2:
                continue
            close = float(col.iloc[-1])
            prev = float(col.iloc[-2])
            high_col = data[("High", yf_sym)].dropna()
            low_col = data[("Low", yf_sym)].dropna()
            open_col = data[("Open", yf_sym)].dropna()
            chg_pct = ((close - prev) / prev * 100) if prev else 0.0
            results[label] = {
                "label": label,
                "symbol": yf_sym,
                "close": close,
                "open": float(open_col.iloc[-1]) if len(open_col) else close,
                "high": float(high_col.iloc[-1]) if len(high_col) else close,
                "low": float(low_col.iloc[-1]) if len(low_col) else close,
                "chg_pct": chg_pct,
                "date": str(col.index[-1].date()),
            }
        except Exception:
            continue

    missing = [
        f"{lab} ({sym})" for lab, sym in label_to_yf.items() if lab not in results
    ]
    if missing:
        log.warning("Yahoo Finance missing: %s", ", ".join(missing))
    log.info("Yahoo Finance (primary): %d/%d symbols fetched", len(results), len(label_to_yf))
    return results


# ── Frankfurter FX (ECB, primary for FX) ─────────────────────────────────────


def fetch_frankfurter_fx() -> dict[str, dict]:
    """Fetch FX rates from Frankfurter API (ECB data, primary FX source).

    Returns ``{label: {label, symbol, close, open, high, low, chg_pct, date}}``
    for each FX pair defined in ``FRANKFURTER_FX``.
    Uses 2-day time series to compute daily change.
    """
    symbols = ",".join(FRANKFURTER_FX.values())
    today = datetime.date.today()
    start = today - datetime.timedelta(days=5)  # weekends buffer
    url = f"https://api.frankfurter.dev/v1/{start}..{today}?base=USD&symbols={symbols}"

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        rates = data.get("rates", {})
        if not rates:
            return {}

        # Need at least 2 trading days to compute change
        sorted_dates = sorted(rates.keys())
        if len(sorted_dates) < 2:
            return {}

        prev_date = sorted_dates[-2]
        last_date = sorted_dates[-1]
        prev_rates = rates[prev_date]
        last_rates = rates[last_date]

        results: dict[str, dict] = {}
        for label, code in FRANKFURTER_FX.items():
            curr = last_rates.get(code)
            prev = prev_rates.get(code)
            if not curr or not prev:
                continue

            # Convert to standard FX quote format
            if label.startswith("USD/"):
                # USD/JPY, USD/CAD, USD/CNH — API returns units per USD, use directly
                close = curr
                open_ = prev
            else:
                # EUR/USD, GBP/USD, AUD/USD — API returns units per USD, invert
                close = round(1.0 / curr, 5)
                open_ = round(1.0 / prev, 5)

            chg_pct = ((close - open_) / open_ * 100) if open_ else 0.0
            results[label] = {
                "label": label,
                "symbol": code,
                "close": close,
                "open": open_,
                "high": close,   # ECB daily fix — no intraday high/low
                "low": close,
                "chg_pct": round(chg_pct, 3),
                "date": last_date,
            }

        if results:
            log.info(
                "Frankfurter FX (primary): %d/%d pairs fetched",
                len(results), len(FRANKFURTER_FX),
            )
        return results

    except Exception as e:
        log.warning("Frankfurter FX failed: %s", e)
        return {}


# ── Stooq CSV (fallback) ────────────────────────────────────────────────────


def fetch_stooq(symbol: str, label: str) -> dict[str, Any] | None:
    """Fetch latest daily OHLC from Stooq CSV endpoint.

    Returns a single-asset dict or ``None`` on failure.
    """
    try:
        url = f"https://stooq.com/q/l/?s={symbol}&f=sd2t2ohlcv&h&e=csv"
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        lines = r.text.strip().splitlines()
        if len(lines) < 2:
            return None
        headers = lines[0].split(",")
        vals = lines[1].split(",")
        row = dict(zip(headers, vals))

        close = float(row.get("Close", 0) or 0)
        open_ = float(row.get("Open", 0) or 0)
        if close == 0 or str(close) == "N/D":
            return None

        chg_pct = ((close - open_) / open_ * 100) if open_ else 0.0
        return {
            "label": label,
            "symbol": symbol,
            "close": close,
            "open": open_,
            "high": float(row.get("High", 0) or 0),
            "low": float(row.get("Low", 0) or 0),
            "chg_pct": chg_pct,
            "date": row.get("Date", ""),
        }
    except Exception as e:
        log.warning("Stooq %s failed: %s", symbol, e)
        return None


# ── Snapshot text formatter ──────────────────────────────────────────────────


def _format_snapshot_text(
    dashboard: DashboardConfig,
    market_results: dict[str, dict],
) -> str:
    """Render the ``=== MARKET SNAPSHOT ===`` text block consumed by Claude."""
    lines: list[str] = ["=== MARKET SNAPSHOT ==="]

    for grp_key, grp_name in _SNAPSHOT_GROUPS:
        items = getattr(dashboard, grp_key, [])
        if not items:
            continue
        fmt = group_fmt(grp_key)
        lines.append(f"\n-- {grp_name} --")
        for item in items:
            d = market_results.get(item.label)
            if d:
                em = dir_emoji(d["chg_pct"])
                lines.append(
                    f"{item.label}: {fmt_val(d['close'], fmt)} {em} {d['chg_pct']:+.1f}%"
                )
            else:
                lines.append(f"{item.label}: N/A")

    return "\n".join(lines)
