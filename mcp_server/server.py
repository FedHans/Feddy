"""MarketBrief MCP Server — expose market intelligence tools to AI assistants.

Run:
    python -m marketbrief.mcp_server              # stdio (Claude Desktop / Claude Code)
    python -m marketbrief.mcp_server --sse 8080    # SSE (remote clients)

Install:
    pip install marketbrief[mcp]
"""

from __future__ import annotations

import json
import logging
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from marketbrief.core.config import MarketBriefConfig

log = logging.getLogger("marketbrief")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

server = Server("marketbrief")

# Global config — initialized once at startup
_cfg: MarketBriefConfig | None = None


def _get_cfg() -> MarketBriefConfig:
    global _cfg
    if _cfg is None:
        _cfg = MarketBriefConfig()
    return _cfg


# ── Tool Definitions ────────────────────────────────────────────────────────

TOOLS = [
    Tool(
        name="generate_report",
        description=(
            "Generate a full AI-powered market briefing report. "
            "Fetches market data, news, and calendar, then uses Claude to produce "
            "structured analysis with tagline, today's focus, 4-issue analysis, "
            "positioning table, news digest, and economic calendar. "
            "Requires ANTHROPIC_API_KEY."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "output_format": {
                    "type": "string",
                    "enum": ["json", "markdown", "html"],
                    "default": "json",
                    "description": "Output format for the report",
                },
                "skip_ai": {
                    "type": "boolean",
                    "default": False,
                    "description": "If true, return data-only report without AI analysis",
                },
            },
        },
    ),
    Tool(
        name="fetch_market_data",
        description=(
            "Fetch current market snapshot — equities, commodities, FX, rates, "
            "volatility, and crypto prices. Uses Yahoo Finance (primary) and "
            "Stooq (fallback). No API key required."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "assets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific asset labels to fetch (e.g. ['S&P 500', 'Gold']). Omit for all.",
                },
                "include_crypto": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include crypto prices from CoinGecko",
                },
            },
        },
    ),
    Tool(
        name="fetch_news",
        description=(
            "Fetch and aggregate news from 40+ RSS feeds covering macro, markets, "
            "crypto, AI/tech, geopolitics, and government sources. "
            "Returns deduplicated items with source, title, URL, and timestamp."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "categories": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by category (e.g. ['crypto', 'macro', 'ai_tech']). Omit for all.",
                },
                "max_items": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of items to return",
                },
                "hours": {
                    "type": "integer",
                    "default": 24,
                    "description": "Only return items from the last N hours",
                },
            },
        },
    ),
    Tool(
        name="fetch_calendar",
        description=(
            "Fetch economic calendar events from Forex Factory, MyFXBook, and FRED. "
            "Returns scheduled data releases, central bank decisions, and other "
            "market-moving events with times, impact levels, and actual values."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date to fetch (ISO format, e.g. '2026-04-07'). Defaults to today.",
                },
                "impact": {
                    "type": "string",
                    "enum": ["high", "medium", "low", "all"],
                    "default": "all",
                    "description": "Filter by impact level",
                },
            },
        },
    ),
    Tool(
        name="analyze_regime",
        description=(
            "Run the macro regime detector — identifies structural market regime "
            "shifts using cross-asset ratios (yield curve, credit conditions, "
            "equity-bond correlation, sector rotation, concentration). "
            "Returns regime classification and confidence scores."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "lookback_days": {
                    "type": "integer",
                    "default": 90,
                    "description": "Number of days of historical data to analyze",
                },
            },
        },
    ),
    Tool(
        name="analyze_breadth",
        description=(
            "Run the market breadth analyzer — measures market participation "
            "using advance/decline ratios, new highs/lows, moving average "
            "crossovers, and divergence signals."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    Tool(
        name="fetch_etf_flows",
        description=(
            "Fetch ETF flow and AUM data for BTC, ETH, and Gold spot ETFs. "
            "Uses SoSoValue API (primary) with RSS fallback."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "assets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Assets to fetch (e.g. ['BTC', 'ETH']). Defaults to all configured.",
                },
            },
        },
    ),
]


@server.list_tools()
async def list_tools():
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    cfg = _get_cfg()

    try:
        if name == "generate_report":
            result = _handle_generate_report(cfg, arguments)
        elif name == "fetch_market_data":
            result = _handle_fetch_market(cfg, arguments)
        elif name == "fetch_news":
            result = _handle_fetch_news(cfg, arguments)
        elif name == "fetch_calendar":
            result = _handle_fetch_calendar(cfg, arguments)
        elif name == "analyze_regime":
            result = _handle_analyze_regime(cfg, arguments)
        elif name == "analyze_breadth":
            result = _handle_analyze_breadth(cfg, arguments)
        elif name == "fetch_etf_flows":
            result = _handle_fetch_etf_flows(cfg, arguments)
        else:
            result = {"error": f"Unknown tool: {name}"}

        text = json.dumps(result, ensure_ascii=False, indent=2, default=str)
        return [TextContent(type="text", text=text)]

    except Exception as e:
        log.error(f"Tool {name} failed: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


# ── Tool Handlers ────────────────────────────────────────────────────────────


def _handle_generate_report(cfg: MarketBriefConfig, args: dict) -> dict:
    from marketbrief.core.pipeline import run_pipeline

    return run_pipeline(
        config_dir=str(cfg.config_dir),
        output_format="json",
        skip_ai=args.get("skip_ai", False),
    )


def _handle_fetch_market(cfg: MarketBriefConfig, args: dict) -> dict:
    from marketbrief.fetchers.market import fetch_market_snapshot

    data = fetch_market_snapshot(cfg)
    # Filter by requested assets if specified
    requested = args.get("assets")
    if requested and isinstance(data, dict) and "prices" in data:
        data["prices"] = {
            k: v for k, v in data["prices"].items() if k in requested
        }
    return data


def _handle_fetch_news(cfg: MarketBriefConfig, args: dict) -> dict:
    from marketbrief.fetchers.news import fetch_news

    items = fetch_news(cfg)
    if not isinstance(items, list):
        return {"items": [], "count": 0}

    # Filter by category
    categories = args.get("categories")
    if categories:
        items = [i for i in items if i.get("category", "") in categories]

    # Filter by hours
    hours = args.get("hours", 24)
    if hours:
        import time
        cutoff = time.time() - (hours * 3600)
        items = [i for i in items if i.get("published_at", 0) >= cutoff]

    # Limit
    max_items = args.get("max_items", 50)
    items = items[:max_items]

    return {"items": items, "count": len(items)}


def _handle_fetch_calendar(cfg: MarketBriefConfig, args: dict) -> dict:
    from marketbrief.fetchers.calendar import fetch_calendar

    events = fetch_calendar(cfg)
    if not isinstance(events, list):
        return {"events": [], "count": 0}

    # Filter by impact
    impact = args.get("impact", "all")
    if impact != "all":
        events = [e for e in events if e.get("impact", "").lower() == impact]

    return {"events": events, "count": len(events)}


def _handle_analyze_regime(cfg: MarketBriefConfig, args: dict) -> dict:
    try:
        from marketbrief.skills.regime_detector import analyze
        return analyze(lookback_days=args.get("lookback_days", 90))
    except ImportError:
        return {"error": "Regime detector skill not yet ported", "status": "stub"}


def _handle_analyze_breadth(cfg: MarketBriefConfig, args: dict) -> dict:
    try:
        from marketbrief.skills.breadth_analyzer import analyze
        return analyze()
    except ImportError:
        return {"error": "Breadth analyzer skill not yet ported", "status": "stub"}


def _handle_fetch_etf_flows(cfg: MarketBriefConfig, args: dict) -> dict:
    from marketbrief.fetchers.etf_flows import fetch_etf_flows

    data = fetch_etf_flows(cfg)
    requested = args.get("assets")
    if requested and isinstance(data, dict):
        data = {k: v for k, v in data.items() if k in requested}
    return data


# ── Entry Point ──────────────────────────────────────────────────────────────


async def run_stdio():
    """Run MCP server over stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """CLI entry point for the MCP server."""
    import asyncio

    if "--sse" in sys.argv:
        try:
            port_idx = sys.argv.index("--sse") + 1
            port = int(sys.argv[port_idx]) if port_idx < len(sys.argv) else 8080
        except (ValueError, IndexError):
            port = 8080

        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Route
        import uvicorn

        sse = SseServerTransport("/messages")

        async def handle_sse(request):
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await server.run(streams[0], streams[1], server.create_initialization_options())

        app = Starlette(routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/messages", endpoint=sse.handle_post_message, methods=["POST"]),
        ])

        log.info(f"Starting MarketBrief MCP server (SSE) on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        log.info("Starting MarketBrief MCP server (stdio)")
        asyncio.run(run_stdio())


if __name__ == "__main__":
    main()
