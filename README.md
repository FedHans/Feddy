# MarketBrief

AI-powered market intelligence framework. Fetch data from 40+ sources, analyze with Claude AI, and deliver daily briefings to Telegram, Feishu, or your terminal.

## Features

- **Multi-source data**: Yahoo Finance, FRED, CoinGecko, SoSoValue, 40+ RSS feeds
- **AI analysis**: Claude generates structured market commentary with source citations
- **Data-only mode**: Works without an AI key — pure market snapshot + news + calendar
- **Configurable assets**: Customize equities, crypto, commodities, FX, and sectors via JSON
- **Multiple outputs**: Telegram HTML, full HTML report, PDF, Markdown, JSON
- **Trading skills**: Macro regime detection, market breadth analysis, sector rotation, exposure coaching
- **MCP Server**: Expose market data tools to any AI assistant
- **Claude Code Skill**: Use as a skill in Claude Code

## Quick Start

```bash
# Install
pip install marketbrief

# Set up config
cp config/portfolio.example.json config/portfolio.json
cp config/dashboard.example.json config/dashboard.json
cp config/feeds.example.json config/feeds.json
cp .env.example .env
# Edit .env with your API keys

# Generate a report (data-only, no AI key needed)
marketbrief generate --no-ai

# Generate with AI analysis
marketbrief generate --output html

# Fetch specific data
marketbrief fetch market
marketbrief fetch news --format table
```

## Configuration

| File | Purpose |
|------|---------|
| `.env` | API keys (Anthropic, FRED, Telegram, etc.) |
| `config/portfolio.json` | Your holdings and watchlist |
| `config/dashboard.json` | Asset groups to track |
| `config/feeds.json` | RSS feed sources |
| `config/prompts/` | Claude system prompts (customizable) |

## MCP Server

```bash
# Install with MCP support
pip install marketbrief[mcp]

# Run as MCP server (stdio)
python -m marketbrief.mcp_server
```

Add to Claude Desktop config:
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

### Available MCP Tools

| Tool | Description | Requires AI Key |
|------|-------------|:-:|
| `generate_report` | Full report pipeline | Yes |
| `fetch_market_data` | Market snapshot | No |
| `fetch_news` | News aggregation | No |
| `fetch_calendar` | Economic calendar | No |
| `analyze_regime` | Macro regime detection | No |
| `analyze_breadth` | Market breadth analysis | No |
| `fetch_etf_flows` | ETF flow data | No |

## GitHub Actions

Template workflows are provided in `workflows/`. Copy to `.github/workflows/` and configure repository secrets:

```bash
cp workflows/morning_report.yml.template .github/workflows/morning_report.yml
```

Required secrets: `ANTHROPIC_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

## Architecture

```
marketbrief generate
    │
    ├── fetchers/     → Yahoo Finance, FRED, RSS, CoinGecko, SoSoValue
    │
    ├── core/analysis → Claude AI structured JSON output
    │
    ├── renderers/    → HTML, Telegram, PDF, Markdown
    │
    └── delivery/     → Telegram, Feishu, stdout
```

## License

MIT
