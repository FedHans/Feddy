"""Claude API orchestration — preflight analysis + report generation.

If ANTHROPIC_API_KEY is not set, the pipeline still works in data-only mode.
"""

from __future__ import annotations

import json
import logging
import re

import anthropic

from marketbrief.core.types import EditorialMemo, PortfolioConfig

log = logging.getLogger("marketbrief")

_PREFLIGHT_SYSTEM = """You are a senior market editor at a Bloomberg-style desk. Before the morning report is written, you analyze today's raw inputs and produce an editorial memo that guides the report writer.

Your job:
1. Read the MARKET SNAPSHOT data to assess today's market regime.
2. Scan all news titles to identify dominant narrative threads.
3. Decide what the report should focus on — and what to kill.

Output a single valid JSON object. No preamble, no markdown fences.

{
  "regime": "risk-off|risk-on|rate-shock|rotation|range-bound|event-driven",
  "regime_signals": ["VIX 22.3 +2.1 → fear", "Gold+DXY both up → safe-haven"],
  "narratives": [
    {
      "thread": "Short narrative label",
      "item_indices": [0, 5, 12, 33],
      "why_it_matters": "One sentence on cross-asset impact"
    }
  ],
  "focus_directive": "2-3 sentences telling the report writer what to lead with.",
  "contrarian_angle": "One under-reported observation that contradicts consensus.",
  "kill_indices": [7, 22, 45],
  "kill_reason": "Brief reason these items add no value"
}

RULES:
- regime: derive from VIX, gold-DXY, yield curve, BTC-equity correlation, ETF flows, oil. Not from news sentiment.
- narratives: max 5 threads. Each must connect 2+ news items.
- kill_indices: flag stale/duplicate items. Be aggressive — kill 30-50%.
- focus_directive: the MOST IMPORTANT field. MAX 3 sentences.
- BREVITY: Total output must be under 2000 tokens.
"""


def _strip_fences(raw: str) -> str:
    """Remove markdown code fences from Claude output."""
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    return raw


def run_preflight(
    api_key: str,
    model: str,
    market_snapshot: str,
    news_titles: list[dict],
    portfolio: PortfolioConfig,
) -> EditorialMemo:
    """Stage 1: editorial thinking layer — lightweight Claude call."""
    if not api_key:
        return EditorialMemo()

    portfolio_str = json.dumps(portfolio.model_dump(), ensure_ascii=False, indent=2)
    titles_block = "\n".join(
        f"[{t['idx']}] ({t['kind']}) {t['title']}" for t in news_titles
    )
    prompt = (
        f"=== PORTFOLIO ===\n{portfolio_str}\n\n"
        f"{market_snapshot}\n\n"
        f"=== NEWS TITLES ({len(news_titles)} items) ===\n{titles_block}"
    )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=model,
            max_tokens=3000,
            system=_PREFLIGHT_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        usage = msg.usage
        log.info(
            f"Pre-flight — input: {usage.input_tokens}, output: {usage.output_tokens} tokens"
        )
        raw = _strip_fences(msg.content[0].text.strip())
        memo = json.loads(raw)
        log.info(
            f"Pre-flight regime: {memo.get('regime', '?')} | "
            f"narratives: {len(memo.get('narratives', []))} | "
            f"kill: {len(memo.get('kill_indices', []))} items"
        )
        return EditorialMemo(**memo)
    except Exception as e:
        log.warning(f"Pre-flight analysis failed (non-fatal): {e}")
        return EditorialMemo()


def run_report(
    api_key: str,
    model: str,
    system_prompt: str,
    market_snapshot: str,
    news_items: list[dict],
    portfolio: PortfolioConfig,
    editorial_memo: EditorialMemo | None = None,
    max_retries: int = 3,
) -> dict:
    """Stage 2: full report generation with editorial guidance.

    Returns parsed JSON dict with _source_index and _editorial_memo.
    """
    if not api_key:
        log.error("ANTHROPIC_API_KEY not set — cannot generate AI report")
        return {"_error": "ANTHROPIC_API_KEY not set"}

    import datetime

    today = datetime.date.today().strftime("%a %b %-d, %Y")
    weekday = datetime.date.today().strftime("%A")
    portfolio_str = json.dumps(portfolio.model_dump(), ensure_ascii=False, indent=2)

    # Build source index
    source_index = []
    items_for_claude = []
    for item in news_items:
        src_refs = []
        for s in item.get("sources", []):
            idx = len(source_index)
            source_index.append({"name": s["name"], "url": s["url"]})
            src_refs.append(f"S{idx}")
        items_for_claude.append({
            "title": item["title"],
            "refs": src_refs,
            "kind": item.get("kind", "news"),
        })

    items_json = json.dumps(items_for_claude, ensure_ascii=False)

    # Build editorial guidance block
    editorial_block = ""
    if editorial_memo and editorial_memo.regime:
        narr_lines = []
        for n in editorial_memo.narratives[:5]:
            narr_lines.append(f"  - {n.get('thread', '')}: {n.get('why_it_matters', '')}")
        editorial_block = (
            f"=== EDITORIAL GUIDANCE ===\n"
            f"REGIME: {editorial_memo.regime}\n"
            f"SIGNALS: {'; '.join(editorial_memo.regime_signals[:4])}\n"
            f"NARRATIVES:\n" + "\n".join(narr_lines) + "\n"
            f"FOCUS: {editorial_memo.focus_directive}\n"
            f"CONTRARIAN: {editorial_memo.contrarian_angle}\n\n"
        )

    prompt = (
        f"TODAY={today}  WEEKDAY={weekday}\n\n"
        f"{editorial_block}"
        f"=== PORTFOLIO ===\n{portfolio_str}\n\n"
        f"{market_snapshot}\n\n"
        f"=== RAW ITEMS ({len(items_for_claude)}) ===\n"
        f"Each item has 'refs' — source indices. Use {{\"ref\": \"S0\"}} format.\n"
        f"{items_json}"
    )

    client = anthropic.Anthropic(api_key=api_key)
    last_error = None
    raw = ""

    for attempt in range(1, max_retries + 1):
        try:
            msg = client.messages.create(
                model=model,
                max_tokens=16000,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
            )
            usage = msg.usage
            log.info(
                f"Claude report (attempt {attempt}/{max_retries}) — "
                f"input: {usage.input_tokens}, output: {usage.output_tokens} tokens"
            )
            raw = _strip_fences(msg.content[0].text.strip())
            parsed = json.loads(raw)
            parsed["_source_index"] = source_index
            if editorial_memo:
                parsed["_editorial_memo"] = editorial_memo.model_dump()
            return parsed
        except json.JSONDecodeError as e:
            last_error = e
            log.warning(f"Invalid JSON (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                continue
        except Exception as e:
            log.error(f"Report API error: {e}")
            return {"_error": str(e), "_source_index": source_index}

    log.error(f"JSON parse failed after {max_retries} attempts: {last_error}")
    return {"_error": f"JSON parse error: {last_error}", "_raw": raw, "_source_index": source_index}
