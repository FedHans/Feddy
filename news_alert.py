import asyncio
from telegram import Bot
import requests
from datetime import datetime
import feedparser
import time
import os
import json

TOKEN = "8798845138:AAGVPd5K9_ItEdqyulLbXA9WpHTHzClTl4c"
CHAT_ID = "7245319588"

# File to store seen articles
SEEN_FILE = "sent_news.json"

def load_seen_articles():
    """Load seen articles from file"""
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_seen_articles(seen_set):
    """Save seen articles to file"""
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen_set), f)

# Load previously seen articles
seen_articles = load_seen_articles()
print(f"📚 Loaded {len(seen_articles)} previously sent articles")

def analyze_impact(title):
    """Simple keyword-based impact analysis"""
    title_lower = title.lower()
    
    bullish_strong = ["surge", "rally", "moon", "all-time high", "ath", "breakthrough", "approval", "inflow record", "massive"]
    bullish = ["gain", "bullish", "approval", "inflow", "adoption", "partnership", "green", "growth", "positive", "up"]
    bearish = ["crash", "decline", "bearish", "reject", "ban", "restrict", "fine", "investigate", "drops", "plunge"]
    bearish_strong = ["collapse", "disaster", "wipeout", "catastrophe", "crisis", "bankruptcy"]
    
    if any(word in title_lower for word in bullish_strong):
        return "🟢 Strongly Bullish", "Strong positive impact expected"
    elif any(word in title_lower for word in bearish_strong):
        return "🔴 Strongly Bearish", "Strong negative impact expected"
    elif any(word in title_lower for word in bullish):
        return "🟢 Bullish", "Positive impact expected"
    elif any(word in title_lower for word in bearish):
        return "🔴 Bearish", "Negative impact expected"
    else:
        return "⚪ Neutral", "No significant impact expected"

async def check_for_news():
    """Check for new crypto news and send alerts"""
    global seen_articles
    bot = Bot(token=TOKEN)
    print(f"🔍 Monitoring for news... (Started at {datetime.now().strftime('%H:%M:%S')})")
    print(f"📰 Loaded {len(seen_articles)} previously sent articles")
    print("📰 Will alert you when news breaks!")
    
    rss_feeds = [
        {"url": "https://cointelegraph.com/rss", "name": "CoinTelegraph"},
        {"url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "name": "CoinDesk"},
        {"url": "https://bitcoinmagazine.com/.rss", "name": "Bitcoin Magazine"},
        {"url": "https://decrypt.co/feed", "name": "Decrypt"}
    ]
    
    while True:
        try:
            for feed_source in rss_feeds:
                try:
                    feed = feedparser.parse(feed_source["url"])
                    
                    for entry in feed.entries[:5]:
                        article_id = entry.link if hasattr(entry, 'link') else entry.title
                        
                        if article_id in seen_articles:
                            continue
                        
                        seen_articles.add(article_id)
                        save_seen_articles(seen_articles)  # Save immediately
                        
                        impact, impact_desc = analyze_impact(entry.title)
                        
                        alert = f"""
⚠️ **NEW CRYPTO NEWS ALERT**

📰 **{entry.title}**

📰 Source: {feed_source['name']}
🕐 Time: {datetime.now().strftime('%H:%M:%S')}
📊 Impact: {impact}

💡 {impact_desc}

🔗 Read more: {entry.link if hasattr(entry, 'link') else 'Link unavailable'}
"""
                        
                        await bot.send_message(chat_id=CHAT_ID, text=alert)
                        print(f"✅ Alert sent: {entry.title[:50]}...")
                        await asyncio.sleep(1)
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"⚠️ Error in main loop: {e}")
        
        await asyncio.sleep(30)

if __name__ == "__main__":
    print("""
============================================================
  📰 Real-Time Crypto News Alerts
  Monitoring: CoinTelegraph, CoinDesk, Bitcoin Magazine, Decrypt
  Sending alerts to Telegram
  Press Ctrl+C to stop
============================================================
""")
    try:
        asyncio.run(check_for_news())
    except KeyboardInterrupt:
        print("\n👋 Stopped monitoring. Goodbye!")
        save_seen_articles(seen_articles)