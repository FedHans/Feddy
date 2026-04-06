---
name: marketbrief
description: Generate AI-powered market intelligence reports with multi-source data (Yahoo Finance, FRED, CoinGecko, 40+ RSS feeds), Claude AI analysis, and multi-channel delivery (Telegram, Feishu, terminal). Trigger when user asks for morning report, market briefing, daily market summary, market snapshot, or wants to analyze market data across equities, crypto, commodities, FX, rates, and economic indicators. Also trigger for economic calendar, news aggregation, or ETF flow data.
---

# MarketBrief — AI-Powered Market Intelligence

Generate comprehensive market briefings that combine multi-source data with Claude AI analysis. Produces structured reports with market commentary, positioning recommendations, economic calendars, and news digests.

## When to Use

- User asks for a "morning report", "market briefing", or "daily summary"
- User wants a market snapshot across equities, crypto, commodities, FX, rates
- User asks about economic calendar or upcoming data releases
- User wants aggregated financial news from multiple sources
- User asks about ETF flows (BTC, ETH, Gold)
- User wants market analysis with structured output (tagline, focus, analysis, positioning)

## Quick Start

### Prerequisites

```bash
pip install marketbrief
# or with MCP support
pip install marketbrief[mcp]
```

### Configuration

1. Copy example configs:
   ```bash
   cp config/portfolio.example.json config/portfolio.json
   cp config/dashboard.example.json config/dashboard.json
   cp config/feeds.example.json config/feeds.json
   cp .env.example .env
   ```

2. Edit `.env` with your API keys:
   - `ANTHROPIC_API_KEY` — Required for AI analysis (optional for data-only mode)
   - `FRED_API_KEY` — Enhances economic data coverage
   - `SOSOVALUE_API_KEY` — ETF flow data
   - `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` — Telegram delivery

3. Edit `config/portfolio.json` with your holdings and interests.

## Workflow

### Generate a Full Report

1. Run the report generator:
   ```bash
   python3 -m marketbrief generate --output json
   ```

2. The pipeline:
   - Fetches market data from Yahoo Finance, FRED, CoinGecko, SoSoValue
   - Aggregates news from 40+ RSS feeds
   - Fetches economic calendar from Forex Factory + FRED
   - Runs Claude AI 2-stage analysis (preflight editorial → structured report)
   - Outputs structured JSON with: tagline, today_focus, analysis (4 issues), positioning, news_digest, calendar

3. Read the output and present to user.

### Data-Only Mode (No API Key)

```bash
python3 -m marketbrief generate --no-ai --output json
```

Returns raw market snapshot, news, and calendar without AI commentary.

### Fetch Specific Data

```bash
python3 -m marketbrief fetch market    # Market prices
python3 -m marketbrief fetch news      # Aggregated news
python3 -m marketbrief fetch calendar  # Economic calendar
python3 -m marketbrief fetch crypto    # Crypto prices
python3 -m marketbrief fetch etf       # ETF flow data
python3 -m marketbrief fetch fred      # FRED economic data
```

### Push to Delivery Channel

```bash
python3 -m marketbrief push --channel telegram
python3 -m marketbrief push --channel feishu
```

## Report Structure

The AI-generated report contains:

| Section | Content |
|---------|---------|
| `tagline` | Bloomberg-style rhyming phrase capturing today's market mood |
| `today_focus` | 3 actionable items: data release, price level, risk catalyst |
| `analysis` | 4 issues, each with: what_happened → market_reaction → contradiction → our_view |
| `positioning` | Stance table (OW/UW/MW/Watch) for portfolio assets |
| `news_digest` | Categorized news briefing with source citations |
| `key_events_today` | 8-12 calendar events with times, impact, actual values |

## MCP Server

MarketBrief can run as an MCP server, exposing 7 tools to any AI assistant:

```bash
python3 -m marketbrief.mcp_server
```

| Tool | What it does | Needs AI Key |
|------|-------------|:---:|
| `generate_report` | Full report pipeline | Yes |
| `fetch_market_data` | Equity, commodity, FX, rates snapshot | No |
| `fetch_news` | 40+ RSS feed aggregation | No |
| `fetch_calendar` | Economic calendar | No |
| `analyze_regime` | Macro regime detection | No |
| `analyze_breadth` | Market breadth analysis | No |
| `fetch_etf_flows` | BTC/ETH/Gold ETF flows | No |

## Data Sources

| Source | Data | Auth |
|--------|------|------|
| Yahoo Finance | Equities, commodities, FX, rates | Free |
| CoinGecko | Crypto prices | Free |
| FRED | Official US economic data | Free API key |
| SoSoValue | ETF AUM & daily flows | API key |
| Forex Factory | Economic calendar | Free |
| 40+ RSS feeds | News from Fed, SEC, CNBC, Bloomberg, CoinDesk, etc. | Free |

## Customization

- **Assets**: Edit `config/dashboard.json` to add/remove tracked assets
- **Portfolio**: Edit `config/portfolio.json` with your holdings
- **News sources**: Edit `config/feeds.json` to customize RSS feeds
- **Analysis style**: Edit `config/prompts/` to customize Claude's output format
- **Delivery**: Configure Telegram or Feishu via `.env`

## Reference Documents

- [Architecture Overview](references/architecture.md)
- [Data Sources Detail](references/data_sources.md)
