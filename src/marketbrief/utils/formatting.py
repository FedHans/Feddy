"""Display helpers — emoji, number formatting, bold wrapping."""

import re

_CRYPTO_PREFIX = {"BTC": "\u20bf", "ETH": "\u039e", "SOL": "\u25ce", "BNB": "\u25cf"}

_BOLD_NUM_RE = re.compile(
    r'(?<![<\w])'
    r'([+\-\u2212]?\$?[\d,]+\.?\d*[KMBTkmbt%]?'
    r'(?:\s*(?:\u2013|\u2014|-)\s*\$?[\d,]+\.?\d*[KMBTkmbt%]?)?'
    r'(?:%|bp|bps)?)'
    r'(?![<\w])'
)


def dir_emoji(pct: float) -> str:
    if pct > 1.0:
        return "\U0001f7e2\u2b06"
    if pct > 0.0:
        return "\U0001f7e1\u2197"
    if pct > -1.0:
        return "\U0001f7e1\u2198"
    return "\U0001f534\u2b07"


def group_fmt(group_key: str) -> str:
    return {"rates": "pct", "volatility": "index", "fx": "fx"}.get(group_key, "price")


def fmt_val(value: float, fmt: str) -> str:
    if fmt == "pct":
        return f"{value:.2f}%"
    elif fmt == "index":
        return f"{value:.2f}"
    elif fmt == "fx":
        return f"{value:.2f}" if value >= 10 else f"{value:.4f}"
    else:
        return f"${value:,.2f}"


def bold_numbers(text: str) -> str:
    """Wrap key numbers in <strong> tags for HTML output."""
    return _BOLD_NUM_RE.sub(r'<strong>\1</strong>', text)


def tg_escape(s) -> str:
    """Escape for Telegram HTML plain text."""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
