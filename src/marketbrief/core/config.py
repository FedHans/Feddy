"""Unified configuration loading.

Priority (most specific wins):
  code defaults < config/*.json < environment variables < CLI arguments
"""

from __future__ import annotations

import json
import logging
import os
import pathlib

from dotenv import load_dotenv

from marketbrief.core.types import (
    AssetConfig,
    DashboardConfig,
    ETFFlowConfig,
    FeedConfig,
    PortfolioConfig,
)

log = logging.getLogger("marketbrief")


class MarketBriefConfig:
    """Central configuration object for the entire pipeline."""

    def __init__(self, config_dir: str | pathlib.Path = "config"):
        self.config_dir = pathlib.Path(config_dir).resolve()

        # Load .env from config_dir parent (project root) or current dir
        for candidate in (self.config_dir.parent / ".env", pathlib.Path(".env")):
            if candidate.exists():
                load_dotenv(candidate, override=True)
                break

        # API keys
        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.fred_api_key = os.environ.get("FRED_API_KEY", "")
        self.sosovalue_api_key = os.environ.get("SOSOVALUE_API_KEY", "")

        # Telegram
        self.telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        self.telegram_channel_id = os.environ.get("TELEGRAM_CHANNEL_ID", "")

        # Feishu
        self.feishu_app_id = os.environ.get("FEISHU_APP_ID", "")
        self.feishu_app_secret = os.environ.get("FEISHU_APP_SECRET", "")
        self.feishu_chat_id = os.environ.get("FEISHU_CHAT_ID", "")

        # Claude model
        self.model = os.environ.get("MARKETBRIEF_MODEL", "claude-haiku-4-5-20251001")

        # Load structured configs
        self.dashboard = self._load_dashboard()
        self.portfolio = self._load_portfolio()
        self.feeds = self._load_feeds()

        # Prompts directory
        self.prompts_dir = self.config_dir / "prompts"

    @property
    def has_ai(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def has_telegram(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)

    @property
    def has_feishu(self) -> bool:
        return bool(self.feishu_app_id and self.feishu_app_secret and self.feishu_chat_id)

    def get_prompt(self, name: str) -> str:
        """Load a prompt file by name (e.g. 'morning_report' → prompts/morning_report.txt)."""
        for ext in (".txt", ".md"):
            path = self.prompts_dir / f"{name}{ext}"
            if path.exists():
                return path.read_text(encoding="utf-8")
        log.warning(f"Prompt '{name}' not found in {self.prompts_dir}")
        return ""

    def get_system_prompt(self) -> str:
        """Build the full system prompt for morning report generation."""
        prompt = self.get_prompt("morning_report")
        if not prompt:
            return "You are a morning market analyst. Output a valid JSON object."

        style = self.get_prompt("style_reference")
        if style:
            prompt += "\n\n===STYLE REFERENCE===\n" + style

        content = self.get_prompt("content_guide")
        if content:
            prompt += "\n\n===CONTENT QUALITY GUIDE===\n" + content

        return prompt

    # ── Private loaders ──────────────────────────────────────────────────────

    def _load_json(self, filename: str) -> dict:
        """Load a JSON file from config_dir, trying both exact name and .example fallback."""
        path = self.config_dir / filename
        if not path.exists():
            example = self.config_dir / f"{path.stem}.example{path.suffix}"
            if example.exists():
                log.info(f"Using example config: {example.name}")
                path = example
            else:
                return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            log.warning(f"Failed to load {filename}: {e}")
            return {}

    def _load_dashboard(self) -> DashboardConfig:
        data = self._load_json("dashboard.json")
        if not data:
            return DashboardConfig()
        # Parse asset configs for each group
        parsed = {}
        for key in ("equities", "precious_metals", "energy", "metals_energy",
                     "rates", "volatility", "fx", "sectors"):
            if key in data:
                parsed[key] = [AssetConfig(**item) for item in data[key]]
        if "crypto_ids" in data:
            parsed["crypto_ids"] = data["crypto_ids"]
        if "etf_flows" in data:
            parsed["etf_flows"] = ETFFlowConfig(**data["etf_flows"])
        return DashboardConfig(**parsed)

    def _load_portfolio(self) -> PortfolioConfig:
        data = self._load_json("portfolio.json")
        if not data:
            return PortfolioConfig()
        return PortfolioConfig(**data)

    def _load_feeds(self) -> list[FeedConfig]:
        data = self._load_json("feeds.json")
        if not data:
            return []
        feeds = []
        for item in data.get("feeds", []):
            # Apply env var override if set
            env_var = item.get("env_var", "")
            url = os.environ.get(env_var, item.get("url", "")) if env_var else item.get("url", "")
            feeds.append(FeedConfig(
                name=item["name"],
                category=item.get("category", ""),
                url=url,
                env_var=env_var,
            ))
        return feeds

    def feeds_by_category(self, category: str) -> list[FeedConfig]:
        """Get feeds filtered by category."""
        return [f for f in self.feeds if f.category == category]
