# MarketBrief Architecture

## Pipeline Overview

```
                    ┌─────────────────────────────────┐
                    │         Configuration            │
                    │  dashboard.json  portfolio.json   │
                    │  feeds.json      .env             │
                    └──────────┬──────────────────────┘
                               │
                    ┌──────────▼──────────────────────┐
                    │      Parallel Data Fetch         │
                    │                                  │
                    │  ┌────────┐  ┌────────┐          │
                    │  │ Market │  │  News  │          │
                    │  │ (yf)   │  │ (RSS)  │          │
                    │  └────────┘  └────────┘          │
                    │  ┌────────┐  ┌────────┐          │
                    │  │Calendar│  │ Crypto │          │
                    │  │(FF/FRED│  │(CoinGk)│          │
                    │  └────────┘  └────────┘          │
                    │  ┌────────┐  ┌────────┐          │
                    │  │ETF Flow│  │  FRED  │          │
                    │  │(SoSoV) │  │ (data) │          │
                    │  └────────┘  └────────┘          │
                    └──────────┬──────────────────────┘
                               │
                    ┌──────────▼──────────────────────┐
                    │   Claude AI (2-stage pipeline)    │
                    │                                  │
                    │  Stage 1: Preflight Editorial     │
                    │  → regime, narratives, kill list  │
                    │                                  │
                    │  Stage 2: Full Report Generation  │
                    │  → structured JSON output         │
                    └──────────┬──────────────────────┘
                               │
                    ┌──────────▼──────────────────────┐
                    │         Renderers                 │
                    │  HTML │ Telegram │ PDF │ Markdown  │
                    └──────────┬──────────────────────┘
                               │
                    ┌──────────▼──────────────────────┐
                    │         Delivery                  │
                    │  Telegram │ Feishu │ stdout        │
                    └─────────────────────────────────┘
```

## Module Structure

```
src/marketbrief/
├── core/
│   ├── config.py      # Unified config: JSON + env vars + CLI args
│   ├── types.py       # Pydantic models for all data structures
│   ├── analysis.py    # Claude API: preflight + report generation
│   └── pipeline.py    # Main orchestrator: fetch → analyze → render → deliver
│
├── fetchers/          # Data acquisition (each returns typed data)
│   ├── market.py      # Yahoo Finance + Stooq fallback
│   ├── news.py        # RSS aggregation (40+ feeds)
│   ├── calendar.py    # Forex Factory + MyFXBook + FRED
│   ├── crypto.py      # CoinGecko API
│   ├── etf_flows.py   # SoSoValue API + RSS fallback
│   └── fred.py        # FRED economic data
│
├── renderers/         # Output formatting
│   ├── html.py        # Full HTML report
│   ├── telegram.py    # Telegram HTML messages
│   ├── pdf.py         # HTML → PDF (Chrome headless)
│   └── markdown.py    # Plain markdown
│
├── delivery/          # Push adapters
│   ├── telegram.py    # Telegram Bot API
│   ├── feishu.py      # Feishu/Lark
│   └── stdout.py      # Terminal output
│
├── skills/            # Modular trading analysis
│   ├── regime_detector/    # Macro regime shifts (7 calculators)
│   ├── breadth_analyzer/   # Market breadth signals
│   ├── exposure_coach/     # Position sizing
│   └── sector_analyst/     # Sector rotation
│
└── cache/             # State persistence
    ├── news_cache.py      # Deduplication across runs
    └── calendar_cache.py  # Calendar event enrichment
```

## Key Design Decisions

1. **Data-only fallback**: If `ANTHROPIC_API_KEY` is not set, the pipeline still produces a useful report with raw market data, news, and calendar — just without AI analysis.

2. **Config hierarchy**: Code defaults → `config/*.json` → environment variables → CLI args. Most specific wins.

3. **Parallel fetching**: All data sources are fetched concurrently via `ThreadPoolExecutor` to minimize latency.

4. **2-stage Claude pipeline**: Stage 1 (preflight) classifies the market regime and identifies narrative threads. Stage 2 (report) uses this editorial guidance to produce higher-quality analysis.

5. **Source indexing**: News items use `[S0]`, `[S1]` reference format. The rendering layer resolves these to clickable hyperlinks. This prevents Claude from hallucinating URLs.
