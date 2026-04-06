# MarketBrief

**Turn 40+ data sources into a daily Wall Street-style market briefing — delivered to your Telegram, automatically.**

MarketBrief is an open-source framework that fetches real-time market data, aggregates news from 40+ RSS feeds, and uses Claude AI to generate structured analyst-grade reports. Think of it as your personal Bloomberg terminal distilled into a daily briefing.

```
Every morning at 7:00 AM, you wake up to this in Telegram:

  "Rates rise, equities capsize"

  TODAY'S FOCUS:
  - CPI 08:30 ET — beat eases Fed, miss reprices June cut
  - Gold $3,100 support — break below = safe-haven bid fading
  - Trump tariff speech 14:00 ET — new China tariffs trigger risk-off

  4 analyst-grade issues with source citations...
  Positioning table (OW/UW/MW)...
  Categorized news digest with 30+ items...
  Economic calendar with 10+ events...
```

---

## What Problem Does This Solve?

If you're a retail investor, crypto trader, or market enthusiast, you probably:
- Check 5-10 websites every morning for market updates
- Miss important economic data releases
- Lack a systematic way to connect dots across asset classes
- Wish you had an analyst writing you a daily briefing

**MarketBrief automates all of this.** It pulls data from official sources (Fed, SEC, FRED, ECB), market data providers (Yahoo Finance, CoinGecko), and 40+ news feeds — then uses Claude AI to synthesize everything into a structured briefing with specific price levels, source citations, and actionable positioning.

---

## How It Works

```
                 YOU CONFIGURE                          IT FETCHES
           ┌─────────────────────┐            ┌──────────────────────┐
           │  portfolio.json     │            │  Yahoo Finance       │
           │  - your holdings    │            │  FRED (official)     │
           │  - interest areas   │            │  CoinGecko           │
           │                     │            │  SoSoValue (ETF)     │
           │  dashboard.json     │            │  Frankfurter (ECB)   │
           │  - assets to track  │            │  40+ RSS feeds       │
           │                     │            │  Forex Factory       │
           │  feeds.json         │            │  MyFXBook            │
           │  - news sources     │            └──────────┬───────────┘
           └─────────┬───────────┘                       │
                     │                                   │
                     ▼                                   ▼
           ┌─────────────────────────────────────────────────────────┐
           │              Claude AI (2-stage pipeline)               │
           │                                                         │
           │  Stage 1: Pre-flight Editorial Analysis                 │
           │  → Identifies market regime (risk-on/off/rotation)      │
           │  → Groups news into narrative threads                   │
           │  → Kills 30-50% of noise items                          │
           │                                                         │
           │  Stage 2: Structured Report Generation                  │
           │  → 4-issue analysis (what/reaction/contradiction/view)  │
           │  → Source-cited positioning table                        │
           │  → Categorized news digest                              │
           │  → Economic calendar with impact scoring                │
           └─────────────────────┬───────────────────────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │ Telegram  │ │  Feishu  │ │ Terminal │
              │ (HTML+PDF)│ │  (Card)  │ │  (JSON)  │
              └──────────┘ └──────────┘ └──────────┘
```

**No AI key? No problem.** Without `ANTHROPIC_API_KEY`, MarketBrief still outputs a complete data-only report: market snapshot, news feed, economic calendar — just without the AI commentary.

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/yukipanpan/marketbrief.git
cd marketbrief
pip install -e .
```

### 2. Configure

```bash
cp config/portfolio.example.json config/portfolio.json
cp config/dashboard.example.json config/dashboard.json
cp config/feeds.example.json config/feeds.json
cp .env.example .env
```

Edit `.env` with your API keys:
```bash
# Required for AI analysis (skip for data-only mode)
ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Optional — enhances data coverage
FRED_API_KEY="your-fred-key"              # Free at https://fred.stlouisfed.org/docs/api/api_key.html
SOSOVALUE_API_KEY="your-sosovalue-key"    # ETF flow data

# Optional — delivery channels
TELEGRAM_BOT_TOKEN="your-bot-token"       # Create at https://t.me/BotFather
TELEGRAM_CHAT_ID="your-chat-id"
```

### 3. Run

```bash
# Data-only mode (no AI key needed, free)
marketbrief generate --no-ai

# Full AI-powered report
marketbrief generate --output json

# Fetch specific data
marketbrief fetch market      # Live prices: equities, FX, commodities, crypto
marketbrief fetch news        # Aggregated news from 40+ feeds
marketbrief fetch calendar    # Economic calendar (Forex Factory + FRED)
marketbrief fetch crypto      # BTC, ETH, SOL prices from CoinGecko
marketbrief fetch etf         # BTC/ETH spot ETF flows from SoSoValue
marketbrief fetch fred        # Official US economic data (CPI, GDP, NFP...)
```

---

## What You Can Customize

This is a **template framework**, not a finished product. Everything is designed to be modified:

### Assets & Portfolio (`config/portfolio.json`)

Track whatever you care about. The default is US-focused, but you can:

```json
{
  "holdings": [
    {"name": "Nikkei 225 ETF", "ticker": "EWJ", "category": "Japan Equities"},
    {"name": "Copper Futures", "ticker": "HG=F", "category": "Industrial Metals"},
    {"name": "Bitcoin", "ticker": "BTC-USD", "category": "Crypto"}
  ],
  "interest_areas": ["Semiconductors", "Uranium", "Japan"],
  "focus_regions": ["Japan", "US", "EU"]
}
```

### Dashboard (`config/dashboard.json`)

Add or remove any asset that Yahoo Finance supports:

```json
{
  "equities": [
    {"label": "Nikkei 225", "yf": "^N225"},
    {"label": "FTSE 100",  "yf": "^FTSE"},
    {"label": "DAX",       "yf": "^GDAXI"}
  ],
  "crypto_ids": ["bitcoin", "ethereum", "solana", "dogecoin"]
}
```

### News Sources (`config/feeds.json`)

Add any RSS feed. Organize by category for smart filtering:

```json
{
  "feeds": [
    {"name": "my_niche_blog", "category": "research", "url": "https://example.com/feed.xml"},
    {"name": "industry_news", "category": "markets",  "url": "https://industry.com/rss"}
  ]
}
```

**Categories matter:** `government` and `geopolitics` feeds are never truncated. `macro` and `ai_tech` feeds get a 7-day lookback (vs 36 hours for news).

### AI Analysis Style (`config/prompts/`)

The Claude prompts are fully editable. You can:
- Change the output language (English, Chinese, or mixed)
- Adjust the number of analysis issues (default: 4)
- Modify the analyst voice (assertive sell-side vs neutral)
- Add custom analysis frameworks
- Change the positioning stance options

---

## Use Cases & Ideas

MarketBrief is a starting point. Here's what you could build with it:

| Use Case | How |
|----------|-----|
| **Personal daily briefing** | Configure your portfolio + Telegram, set up GitHub Actions cron |
| **Crypto-focused tracker** | Remove equities, add 20 crypto feeds, track DeFi protocols |
| **Macro research assistant** | Heavy on FRED + Fed + Treasury feeds, focus on rates/FX |
| **Team morning standup** | Push to a shared Telegram channel or Feishu group |
| **AI agent data source** | Use the MCP Server to give any AI assistant live market data |
| **Trading signal pipeline** | Add your own scoring logic to the news/calendar fetchers |
| **Multi-language briefing** | Change `OUTPUT_LANGUAGE` in the prompt to Chinese/Japanese |
| **Earnings season tracker** | Add earnings-focused RSS feeds, customize calendar filtering |

---

## MCP Server

MarketBrief can run as an [MCP](https://modelcontextprotocol.io/) server, letting any AI assistant (Claude Desktop, Claude Code, etc.) call market data tools directly.

```bash
pip install marketbrief[mcp]
python -m marketbrief.mcp_server
```

Add to your Claude Desktop config (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "marketbrief": {
      "command": "python",
      "args": ["-m", "marketbrief.mcp_server"],
      "env": {"FRED_API_KEY": "your-key"}
    }
  }
}
```

### 7 Available Tools

| Tool | What It Does | Needs AI Key |
|------|-------------|:---:|
| `generate_report` | Full AI-powered briefing pipeline | Yes |
| `fetch_market_data` | Equities, commodities, FX, rates, crypto snapshot | No |
| `fetch_news` | Aggregate 40+ RSS feeds with deduplication | No |
| `fetch_calendar` | Economic calendar (Forex Factory + MyFXBook) | No |
| `analyze_regime` | Macro regime detection (yield curve, credit, rotation) | No |
| `analyze_breadth` | Market breadth signals (advance/decline, MA crossovers) | No |
| `fetch_etf_flows` | BTC/ETH spot ETF daily flows and AUM | No |

Most tools work **without any API key** — only `generate_report` needs Anthropic.

---

## Automated Delivery (GitHub Actions)

Run MarketBrief on a schedule — no server needed:

1. Copy the workflow template:
   ```bash
   mkdir -p .github/workflows
   cp workflows/morning_report.yml.template .github/workflows/morning_report.yml
   ```

2. Add secrets in your GitHub repo (Settings → Secrets → Actions):
   - `ANTHROPIC_API_KEY`
   - `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`
   - `FRED_API_KEY` (optional)

3. Adjust the cron schedule for your timezone (see `workflows/README.md`).

4. Push — reports will be generated and delivered automatically.

---

## Data Sources

| Source | Data | Cost |
|--------|------|:----:|
| Yahoo Finance | Equities, commodities, FX, rates, sectors | Free |
| Frankfurter API | ECB official exchange rates | Free |
| CoinGecko | Crypto prices + market cap | Free |
| FRED | Official US economic data (CPI, GDP, NFP, yields) | Free (API key) |
| SoSoValue | BTC/ETH spot ETF daily flows + AUM | Free (API key) |
| Forex Factory | Economic calendar with times + impact | Free |
| MyFXBook | Calendar with actual/forecast/previous | Free |
| 40+ RSS feeds | News from Fed, SEC, CNBC, Bloomberg, CoinDesk, etc. | Free |

---

## Project Structure

```
marketbrief/
├── src/marketbrief/
│   ├── core/
│   │   ├── config.py       # Unified config: JSON + env vars
│   │   ├── types.py        # Pydantic models for all data
│   │   ├── analysis.py     # Claude AI 2-stage pipeline
│   │   └── pipeline.py     # Main orchestrator
│   ├── fetchers/            # 6 data source modules
│   ├── renderers/           # HTML, Telegram, PDF, Markdown
│   ├── delivery/            # Telegram, Feishu, stdout
│   └── skills/              # Trading analysis modules
├── config/                  # Customizable JSON configs + prompts
├── mcp_server/              # MCP Server (7 tools)
├── claude_skill/            # Claude Code Skill definition
└── workflows/               # GitHub Actions templates
```

---

## Contributing

PRs welcome! Some areas where contributions would be especially valuable:

- **New fetchers**: Add data sources (e.g., Binance, TradingView, Alpha Vantage)
- **Renderers**: Improve HTML/PDF output, add new formats (Slack, Discord, email)
- **Trading skills**: Port regime detector and breadth analyzer
- **Localization**: Prompts for other languages (Japanese, Korean, Spanish)
- **Tests**: Unit tests for fetchers and the analysis pipeline

---

## License

MIT — use it however you want.
