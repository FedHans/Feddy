"""Pydantic models for all data structures flowing through the pipeline."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ── Market Data ──────────────────────────────────────────────────────────────


class AssetConfig(BaseModel):
    """A single tracked asset (equity, FX pair, commodity, etc.)."""
    label: str
    stooq: str = ""
    yf: str = ""
    note: str = ""


class AssetPrice(BaseModel):
    """Price snapshot for a single asset."""
    label: str
    price: float = 0.0
    change_pct: float = 0.0
    prev_close: float = 0.0
    source: str = ""  # "yfinance", "stooq", "frankfurter"


class CryptoPrice(BaseModel):
    """CoinGecko crypto price."""
    id: str
    symbol: str = ""
    price_usd: float = 0.0
    change_24h_pct: float = 0.0
    market_cap: float = 0.0


class ETFFlowData(BaseModel):
    """ETF AUM and flow data (SoSoValue or RSS)."""
    asset: str  # "BTC", "ETH"
    aum_b: Optional[float] = None
    daily_flow_m: Optional[float] = None
    source: str = ""
    date: str = ""


class FREDSeries(BaseModel):
    """A single FRED data point."""
    series_id: str
    label: str
    value: float
    date: str
    unit: str = ""


class MarketSnapshot(BaseModel):
    """Complete market data for one report cycle."""
    prices: list[AssetPrice] = Field(default_factory=list)
    crypto: list[CryptoPrice] = Field(default_factory=list)
    etf_flows: list[ETFFlowData] = Field(default_factory=list)
    fred_latest: dict[str, FREDSeries] = Field(default_factory=dict)
    fx_rates: dict[str, float] = Field(default_factory=dict)
    snapshot_text: str = ""  # pre-formatted text block for Claude


# ── News ─────────────────────────────────────────────────────────────────────


class NewsSource(BaseModel):
    """A source reference for a news item."""
    name: str
    url: str


class NewsItem(BaseModel):
    """A single news item from RSS, SoSoValue, or other source."""
    title: str
    url: str = ""
    source: str = ""
    sources: list[NewsSource] = Field(default_factory=list)
    score: float = 0.0
    published_at: int = 0  # epoch timestamp
    kind: str = "news"  # "news" or "research"
    category: str = ""
    consumed: bool = False


# ── Calendar ─────────────────────────────────────────────────────────────────


class CalendarEvent(BaseModel):
    """An economic calendar event."""
    time: str  # "08:30 ET", "2026-04-03", "Mon Mar 28"
    name: str
    impact: str = "medium"  # "high", "medium", "low"
    status: str = "upcoming"  # "upcoming" or "released"
    actual: str = ""
    bullets: list[str] = Field(default_factory=list)
    source: str = ""  # "ff", "myfxbook", "fred", "claude"
    country: str = ""


# ── Report Output ────────────────────────────────────────────────────────────


class AnalysisIssue(BaseModel):
    """One issue in the analysis section."""
    emoji: str = ""
    title: str
    what_happened: list[str] = Field(default_factory=list)
    market_reaction: list[str] = Field(default_factory=list)
    contradiction: list[str] = Field(default_factory=list)
    our_view: list[str] = Field(default_factory=list)
    metrics: list[dict] = Field(default_factory=list)


class PositioningEntry(BaseModel):
    """A single positioning stance."""
    asset: str
    ticker: str = ""
    stance: str  # "OW", "UW", "MW", "Watch"
    conviction: str = "Medium"  # "High", "Medium", "Low"
    rationale: str = ""


class NewsDigestItem(BaseModel):
    """A single news digest entry."""
    title: str
    comment: str = ""
    refs: list[str] = Field(default_factory=list)


class NewsDigestCategory(BaseModel):
    """A categorized group of news digest items."""
    category: str
    items: list[NewsDigestItem] = Field(default_factory=list)


class EditorialMemo(BaseModel):
    """Pre-flight editorial analysis output."""
    regime: str = ""
    regime_signals: list[str] = Field(default_factory=list)
    narratives: list[dict] = Field(default_factory=list)
    focus_directive: str = ""
    contrarian_angle: str = ""
    kill_indices: list[int] = Field(default_factory=list)
    kill_reason: str = ""


class ReportData(BaseModel):
    """Complete structured report output from Claude."""
    tagline: str = ""
    today_focus: list[str] = Field(default_factory=list)
    analysis: list[AnalysisIssue] = Field(default_factory=list)
    positioning: list[PositioningEntry] = Field(default_factory=list)
    news_digest: list[NewsDigestCategory] = Field(default_factory=list)
    key_events_today: list[CalendarEvent] = Field(default_factory=list)
    source_index: list[NewsSource] = Field(default_factory=list)
    editorial_memo: Optional[EditorialMemo] = None


# ── Pipeline Config ──────────────────────────────────────────────────────────


class FeedConfig(BaseModel):
    """A single RSS feed definition."""
    name: str
    category: str
    url: str
    env_var: str = ""


class ETFFlowConfig(BaseModel):
    """ETF flow tracking config."""
    btc_etf: bool = True
    eth_etf: bool = True
    gold_etf: bool = False


class DashboardConfig(BaseModel):
    """Which assets to track and display."""
    equities: list[AssetConfig] = Field(default_factory=list)
    precious_metals: list[AssetConfig] = Field(default_factory=list)
    energy: list[AssetConfig] = Field(default_factory=list)
    metals_energy: list[AssetConfig] = Field(default_factory=list)
    rates: list[AssetConfig] = Field(default_factory=list)
    volatility: list[AssetConfig] = Field(default_factory=list)
    fx: list[AssetConfig] = Field(default_factory=list)
    sectors: list[AssetConfig] = Field(default_factory=list)
    crypto_ids: list[str] = Field(default_factory=lambda: ["bitcoin", "ethereum", "solana"])
    etf_flows: ETFFlowConfig = Field(default_factory=ETFFlowConfig)


class PortfolioConfig(BaseModel):
    """User's holdings and interests."""
    holdings: list[dict] = Field(default_factory=list)
    watchlist: list[str] = Field(default_factory=list)
    interest_areas: list[str] = Field(default_factory=list)
    focus_regions: list[str] = Field(default_factory=list)
    hotspot_regions: list[str] = Field(default_factory=list)
