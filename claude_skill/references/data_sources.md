# MarketBrief Data Sources

## Market Data

| Source | Data | Auth | Reliability |
|--------|------|------|-------------|
| **Yahoo Finance** (primary) | Equities, commodities, FX, rates, sectors | None (free) | High — batch fetch via `yfinance` library |
| **Stooq** (fallback) | Same asset classes | None (free) | Medium — used only when Yahoo fails |
| **Frankfurter API** (FX) | ECB official exchange rates | None (free) | High — official ECB data |

## Crypto

| Source | Data | Auth |
|--------|------|------|
| **CoinGecko** | BTC, ETH, SOL, BNB prices + 24h change + market cap | None (free, rate-limited) |

## ETF Flows

| Source | Data | Auth | Priority |
|--------|------|------|----------|
| **SoSoValue API** | BTC/ETH spot ETF daily flows + AUM | API key (`SOSOVALUE_API_KEY`) | Primary — most authoritative |
| **RSS feeds** | ETF flow headlines | None | Fallback — used when SoSoValue unavailable |

## Economic Data

| Source | Data | Auth |
|--------|------|------|
| **FRED** | Official US indicators (CPI, PPI, GDP, NFP, PCE, yields) | API key (`FRED_API_KEY`) |
| **Forex Factory** | Economic calendar with times and impact levels | None (JSON endpoint) |
| **MyFXBook** | Calendar with actual/forecast/previous values | None (RSS) |

## News (40+ RSS Feeds)

### Macro & Markets
- Federal Reserve press releases
- BEA economic data releases
- CNBC Economy, CNBC Investing
- Bloomberg Markets
- WSJ Markets (Dow Jones)
- MarketWatch Bulletins
- Seeking Alpha Market Currents
- Reuters Markets, Reuters World

### Government & Regulatory
- White House
- US Treasury press releases
- SEC press releases + speeches
- OCC, FDIC, DOJ, CFTC

### Crypto
- CoinDesk Markets, CoinDesk Policy
- Cointelegraph
- Decrypt
- BlockBeats
- Arthur Hayes (Medium)

### Research & Institutional
- Morgan Stanley Insights
- Goldman Sachs Insights
- JPM Research
- ARK Invest
- Citadel
- Barclays, Nomura
- A16Z (Crypto, AI, Build)
- Galaxy Digital
- Sequoia
- Glassnode, INET

### AI & Tech
- NVIDIA Blog
- OpenAI Blog
- DeepMind Blog
- Meta AI Engineering
- Anthropic Blog

### Geopolitics & China
- Xinhua News Agency
- Global Times
- Tasnim News Agency (Iran, EN + FA)
- Breaking The News

## Feed Configuration

Feeds are defined in `config/feeds.json`. Each entry has:
- `name`: identifier
- `category`: for filtering (macro, markets, crypto, ai_tech, news, china, government, geopolitics)
- `url`: RSS feed URL
- `env_var`: optional environment variable override

Users can add/remove feeds by editing `feeds.json`. No code changes needed.
