"""Main orchestrator: fetch → analyze → render → deliver.

This is the heart of MarketBrief. It coordinates all pipeline stages.
"""

from __future__ import annotations

import datetime
import json
import logging
import sys

from marketbrief.core.config import MarketBriefConfig
from marketbrief.core.types import MarketSnapshot, ReportData

log = logging.getLogger("marketbrief")


def run_pipeline(
    config_dir: str = "config",
    output_format: str = "stdout",
    skip_ai: bool = False,
) -> dict:
    """Full pipeline: fetch data → (optional) Claude analysis → render → output.

    Args:
        config_dir: Path to configuration directory.
        output_format: One of "stdout", "html", "pdf", "json", "markdown".
        skip_ai: If True, skip Claude analysis and output data-only report.

    Returns:
        Dict with report data and metadata.
    """
    cfg = MarketBriefConfig(config_dir)

    if skip_ai or not cfg.has_ai:
        if not skip_ai:
            log.info("No ANTHROPIC_API_KEY — running in data-only mode")
        return _run_data_only(cfg, output_format)

    return _run_full(cfg, output_format)


def _run_data_only(cfg: MarketBriefConfig, output_format: str) -> dict:
    """Data-only pipeline: fetch and format without AI analysis."""
    import concurrent.futures

    from marketbrief.fetchers.market import fetch_market_snapshot
    from marketbrief.fetchers.news import fetch_news
    from marketbrief.fetchers.calendar import fetch_calendar

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        mkt_future = ex.submit(fetch_market_snapshot, cfg)
        news_future = ex.submit(fetch_news, cfg)
        cal_future = ex.submit(fetch_calendar, cfg)

        snapshot = mkt_future.result()
        news_items = news_future.result()
        calendar_events = cal_future.result()

    result = {
        "snapshot": snapshot,
        "news": news_items,
        "calendar": calendar_events,
        "generated_at": datetime.datetime.now().isoformat(),
        "mode": "data-only",
    }

    _output(result, output_format)
    return result


def _run_full(cfg: MarketBriefConfig, output_format: str) -> dict:
    """Full pipeline with Claude AI analysis."""
    import concurrent.futures

    from marketbrief.core.analysis import run_preflight, run_report
    from marketbrief.fetchers.market import fetch_market_snapshot
    from marketbrief.fetchers.news import fetch_news
    from marketbrief.fetchers.calendar import fetch_calendar

    # Stage 0: Parallel data fetch
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        mkt_future = ex.submit(fetch_market_snapshot, cfg)
        news_future = ex.submit(fetch_news, cfg)
        cal_future = ex.submit(fetch_calendar, cfg)

        snapshot = mkt_future.result()
        news_items = news_future.result()
        calendar_events = cal_future.result()

    # Build snapshot text for Claude
    snapshot_text = snapshot.get("text", "") if isinstance(snapshot, dict) else str(snapshot)
    if calendar_events:
        cal_text = "\n".join(
            f"  {e.get('time', '')} | {e.get('name', '')} | {e.get('impact', '')}"
            for e in (calendar_events if isinstance(calendar_events, list) else [])
        )
        snapshot_text += f"\n\n-- ECONOMIC CALENDAR --\n{cal_text}"

    # Stage 1: Preflight editorial analysis
    news_titles = [
        {"idx": i, "title": item.get("title", ""), "kind": item.get("kind", "news")}
        for i, item in enumerate(news_items if isinstance(news_items, list) else [])
    ]
    editorial_memo = run_preflight(
        api_key=cfg.anthropic_api_key,
        model=cfg.model,
        market_snapshot=snapshot_text,
        news_titles=news_titles,
        portfolio=cfg.portfolio,
    )

    # Apply kill list
    kill_set = set(editorial_memo.kill_indices)
    items = news_items if isinstance(news_items, list) else []
    if kill_set:
        surviving = [item for i, item in enumerate(items) if i not in kill_set]
        log.info(f"Kill list: {len(items)} → {len(surviving)} items")
        items = surviving

    # Stage 2: Full report generation
    system_prompt = cfg.get_system_prompt()
    report_data = run_report(
        api_key=cfg.anthropic_api_key,
        model=cfg.model,
        system_prompt=system_prompt,
        market_snapshot=snapshot_text,
        news_items=items,
        portfolio=cfg.portfolio,
        editorial_memo=editorial_memo,
    )

    result = {
        "report": report_data,
        "snapshot": snapshot,
        "calendar": calendar_events,
        "generated_at": datetime.datetime.now().isoformat(),
        "mode": "full",
    }

    _output(result, output_format)
    return result


def _output(result: dict, fmt: str):
    """Output result in the requested format."""
    if fmt == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    elif fmt == "stdout":
        _print_summary(result)
    elif fmt in ("html", "pdf", "markdown"):
        # TODO: delegate to renderers
        log.info(f"Output format '{fmt}' — renderer not yet implemented, falling back to JSON")
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


def _print_summary(result: dict):
    """Print a human-readable summary to stdout."""
    mode = result.get("mode", "unknown")
    generated = result.get("generated_at", "")

    print(f"\n{'='*60}")
    print(f"  MarketBrief — {mode} mode")
    print(f"  Generated: {generated}")
    print(f"{'='*60}\n")

    report = result.get("report", {})
    if report and not report.get("_error"):
        tagline = report.get("tagline", "")
        if tagline:
            print(f"  {tagline}\n")

        focus = report.get("today_focus", [])
        if focus:
            print("  TODAY'S FOCUS:")
            for item in focus:
                print(f"    - {item}")
            print()

        analysis = report.get("analysis", [])
        if analysis:
            print(f"  ANALYSIS ({len(analysis)} issues):")
            for issue in analysis:
                title = issue.get("title", "") if isinstance(issue, dict) else str(issue)
                print(f"    {title}")
            print()

    snapshot = result.get("snapshot", {})
    if isinstance(snapshot, dict) and snapshot.get("text"):
        lines = snapshot["text"].split("\n")[:20]
        print("  MARKET SNAPSHOT (first 20 lines):")
        for line in lines:
            print(f"    {line}")


def run_fetch(source: str, output_format: str = "json"):
    """Fetch a single data source and output."""
    cfg = MarketBriefConfig()

    if source == "market":
        from marketbrief.fetchers.market import fetch_market_snapshot
        data = fetch_market_snapshot(cfg)
    elif source == "news":
        from marketbrief.fetchers.news import fetch_news
        data = fetch_news(cfg)
    elif source == "calendar":
        from marketbrief.fetchers.calendar import fetch_calendar
        data = fetch_calendar(cfg)
    elif source == "crypto":
        from marketbrief.fetchers.crypto import fetch_crypto
        data = fetch_crypto(cfg)
    elif source == "etf":
        from marketbrief.fetchers.etf_flows import fetch_etf_flows
        data = fetch_etf_flows(cfg)
    elif source == "fred":
        from marketbrief.fetchers.fred import fetch_fred_latest
        data = fetch_fred_latest(cfg)
    elif source == "all":
        return run_pipeline(output_format=output_format, skip_ai=True)
    else:
        log.error(f"Unknown source: {source}")
        sys.exit(1)

    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def run_push(channel: str, report_path: str | None = None):
    """Push a report to a delivery channel."""
    cfg = MarketBriefConfig()

    if channel == "telegram":
        if not cfg.has_telegram:
            log.error("Telegram not configured — set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
            sys.exit(1)
        from marketbrief.delivery.telegram import push_report
        push_report(cfg, report_path)
    elif channel == "feishu":
        if not cfg.has_feishu:
            log.error("Feishu not configured — set FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_CHAT_ID")
            sys.exit(1)
        from marketbrief.delivery.feishu import push_report
        push_report(cfg, report_path)
    elif channel == "stdout":
        log.info("stdout channel — nothing to push")
    else:
        log.error(f"Unknown channel: {channel}")
        sys.exit(1)
