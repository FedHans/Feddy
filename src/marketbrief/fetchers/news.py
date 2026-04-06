"""News fetcher — RSS feeds with parallel fetching and deduplication.

Ports fetch_rss_feed(), fetch_morning_news(), dedup_news_items() from
the legacy morning_fetchers.py into a clean, config-driven module.
"""

from __future__ import annotations

import calendar
import concurrent.futures
import logging
import random
import re
import time

import feedparser

from marketbrief.core.config import MarketBriefConfig

log = logging.getLogger("marketbrief")

# ── Categories that count as "research" (longer recency window) ─────────────
_RESEARCH_CATEGORIES = {"macro", "ai_tech"}

# rss.app institutional feeds are also research regardless of category
_RSSAPP_INSTITUTIONAL_MARKER = "rss.app"

# ── Categories whose sources are never truncated by RELEVANT_CAP ────────────
_PRIORITY_CATEGORIES = {"government", "geopolitics"}

# ── Interest keywords for relevance filtering ──────────────────────────────
_INTEREST_KEYWORDS = [
    "ai", "gold", "crypto", "bitcoin", "energy", "oil",
    "fed", "rate", "inflation", "gdp", "market", "semiconductor",
    "china", "iran",
]

# ── Subscription/spam title fragments to skip ──────────────────────────────
_SKIP_TITLES = [
    "confirm your subscription",
    "welcome to",
    "please confirm",
    "thank you for subscribing",
    "you're on the list",
]

# ── Stopwords for title normalisation ──────────────────────────────────────
_STOPWORDS = frozenset({
    "the", "a", "an", "in", "on", "at", "to", "for", "of", "is", "are",
    "was", "as", "by", "with", "from", "says", "said", "report", "reports",
})


# ═══════════════════════════════════════════════════════════════════════════
# Single-feed fetcher
# ═══════════════════════════════════════════════════════════════════════════

def fetch_rss_feed(url: str, source_name: str, n: int = 20) -> list[dict]:
    """Fetch a single RSS feed, returning up to *n* normalised items.

    Each item is ``{source, title, url, score, published_at}`` where
    *published_at* is a UTC epoch integer.
    """
    try:
        feed = feedparser.parse(url)
        items: list[dict] = []
        for entry in feed.entries[:n]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "")

            # Skip rss.app email-feed confirmation links
            if "rss.app/emailfeed/" in link:
                continue

            # Skip subscription confirmation titles
            if any(kw in title.lower() for kw in _SKIP_TITLES):
                continue

            pub_parsed = entry.get("published_parsed")
            pub_epoch = calendar.timegm(pub_parsed) if pub_parsed else 0

            items.append({
                "source": source_name,
                "title": title,
                "url": link,
                "score": 0,
                "published_at": pub_epoch,
            })
        return items
    except Exception as exc:
        log.warning("RSS %s failed: %s", source_name, exc)
        return []


# ═══════════════════════════════════════════════════════════════════════════
# Main news aggregator
# ═══════════════════════════════════════════════════════════════════════════

def _classify_kind(feed) -> str:
    """Return 'research' or 'news' for a FeedConfig."""
    if feed.category in _RESEARCH_CATEGORIES:
        return "research"
    if _RSSAPP_INSTITUTIONAL_MARKER in feed.url:
        return "research"
    return "news"


def fetch_news(cfg: MarketBriefConfig) -> list[dict]:
    """Fetch news from all configured RSS feeds.

    Returns a unified list of item dicts, each containing at minimum:
    ``{source, title, url, score, published_at, kind, category}``.
    """
    RELEVANT_CAP = 60
    WILDCARD_CAP = 20

    if not cfg.feeds:
        log.warning("No feeds configured — returning empty news list")
        return []

    # ── Build feed tasks with kind classification ───────────────────────
    feed_tasks: list[tuple] = []  # (FeedConfig, kind)
    for feed in cfg.feeds:
        if not feed.url:
            continue
        kind = _classify_kind(feed)
        feed_tasks.append((feed, kind))

    # ── Parallel fetch ──────────────────────────────────────────────────
    raw: dict[str, list[dict]] = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        future_map = {
            executor.submit(fetch_rss_feed, feed.url, feed.name, 20): (feed, kind)
            for feed, kind in feed_tasks
        }

        for future in concurrent.futures.as_completed(future_map):
            feed, kind = future_map[future]
            try:
                items = future.result()
            except Exception as exc:
                log.warning("Feed %s raised: %s", feed.name, exc)
                items = []
            for item in items:
                item["kind"] = kind
                item["category"] = feed.category
            raw[feed.name] = items

    # ── Recency filters ─────────────────────────────────────────────────
    now = time.time()
    news_cutoff = now - 36 * 3600        # 36 hours
    research_cutoff = now - 7 * 86400    # 7 days

    news_items: list[dict] = []
    research_items: list[dict] = []

    for items in raw.values():
        for item in items:
            pub = item.get("published_at", 0)
            if item["kind"] == "research":
                if not pub or pub >= research_cutoff:
                    research_items.append(item)
            else:
                if not pub or pub >= news_cutoff:
                    news_items.append(item)

    # ── Bucket news into priority / relevant / other ────────────────────
    priority_news: list[dict] = []
    relevant_news: list[dict] = []
    other_news: list[dict] = []

    for item in news_items:
        cat = item.get("category", "")
        if cat in _PRIORITY_CATEGORIES:
            priority_news.append(item)
        elif any(kw in item["title"].lower() for kw in _INTEREST_KEYWORDS):
            relevant_news.append(item)
        else:
            other_news.append(item)

    wildcard = random.sample(other_news, min(WILDCARD_CAP, len(other_news)))
    selected_news = priority_news + relevant_news[:RELEVANT_CAP] + wildcard

    if priority_news:
        log.info(
            "Priority sources: %d items from %s",
            len(priority_news),
            {i["source"] for i in priority_news},
        )

    log.info(
        "Feed buckets: %d relevant + %d wildcard news, %d research (7d)",
        len(relevant_news),
        len(wildcard),
        len(research_items),
    )

    return selected_news + research_items


# ═══════════════════════════════════════════════════════════════════════════
# Title normalisation helpers
# ═══════════════════════════════════════════════════════════════════════════

def _normalize_title(title: str) -> str:
    """Lowercase, strip punctuation and stopwords for similarity comparison."""
    t = title.lower().strip()
    t = re.sub(r"[^\w\s]", "", t)
    words = [w for w in t.split() if w not in _STOPWORDS and len(w) > 2]
    return " ".join(words)


def _word_overlap(a: str, b: str) -> float:
    """Jaccard similarity on word sets."""
    wa, wb = set(a.split()), set(b.split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


# ═══════════════════════════════════════════════════════════════════════════
# Deduplication
# ═══════════════════════════════════════════════════════════════════════════

def dedup_news_items(items: list[dict], threshold: float = 0.55) -> list[dict]:
    """Merge items about the same event into one, preserving all source URLs.

    Returns a list where each item may have multiple sources::

        {
            "title": "best (longest) title",
            "sources": [{"name": "reuters", "url": "..."}, ...],
            "kind": "news",
            "published_at": <max epoch across cluster>,
        }
    """
    if not items:
        return []

    normed = [(_normalize_title(i["title"]), i) for i in items]
    used = [False] * len(normed)
    merged: list[dict] = []

    for i, (ni, item_i) in enumerate(normed):
        if used[i]:
            continue

        cluster = [item_i]
        used[i] = True

        for j in range(i + 1, len(normed)):
            if used[j]:
                continue
            nj = normed[j][0]
            if _word_overlap(ni, nj) >= threshold:
                cluster.append(normed[j][1])
                used[j] = True

        # Pick the longest title as the representative
        best = max(cluster, key=lambda x: len(x["title"]))

        # Collect unique source URLs
        sources: list[dict] = []
        seen_urls: set[str] = set()
        for c in cluster:
            url = c.get("url", "")
            if url and url not in seen_urls:
                sources.append({"name": c["source"], "url": url})
                seen_urls.add(url)

        merged.append({
            "title": best["title"],
            "sources": sources,
            "kind": best.get("kind", "news"),
            "published_at": max(c.get("published_at", 0) for c in cluster),
        })

    return merged
