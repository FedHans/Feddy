import asyncio
from telegram import Bot
import requests
from datetime import datetime
import feedparser
import time

TOKEN = "8798845138:AAGVPd5K9_ItEdqyulLbXA9WpHTHzClTl4c"
CHAT_ID = "7245319588"

# Track seen articles to avoid duplicates
seen_articles = set()

def analyze_impact(title):
    """Simple keyword-based impact analysis"""
    title_lower = title.lower()
    
    # Strong bullish keywords
    bullish_strong = ["surge", "rally", "moon", "all-time high", "ath", "breakthrough", "approval", "inflow record", "massive"]
    # Bullish keywords
    bullish = ["gain", "bullish", "approval", "inflow", "adoption", "partnership", "green", "growth", "positive", "up"]
    # Bearish keywords
    bearish = ["crash", "decline", "bearish", "reject", "ban", "restrict", "fine", "investigate", "drops", "plunge"]
    # Strong bearish keywords
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
    bot = Bot(token=TOKEN)
    print(f"🔍 Monitoring for news... (Started at {datetime.now().strftime('%H:%M:%S')})")
    print("📰 Will alert you when news breaks!")
    
    # RSS feeds to monitor
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
                    
                    # Get latest entries (check new ones)
                    for entry in feed.entries[:5]:
                        article_id = entry.link if hasattr(entry, 'link') else entry.title
                        
                        # Skip if already seen
                        if article_id in seen_articles:
                            continue
                        
                        # Add to seen
                        seen_articles.add(article_id)
                        
                        # Analyze impact
                        impact, impact_desc = analyze_impact(entry.title)
                        
                        # Build alert message
                        alert = f"""
⚠️ **NEW CRYPTO NEWS ALERT**

📰 **{entry.title}**

📰 Source: {feed_source['name']}
🕐 Time: {datetime.now().strftime('%H:%M:%S')}
📊 Impact: {impact}

💡 {impact_desc}

🔗 Read more: {entry.link if hasattr(entry, 'link') else 'Link unavailable'}
"""
                        
                        # Send alert to Telegram
                        await bot.send_message(chat_id=CHAT_ID, text=alert)
                        print(f"✅ Alert sent: {entry.title[:50]}...")
                        
                        # Small delay to avoid rate limiting
                        await asyncio.sleep(1)
                        
                except Exception as e:
                    # If one feed fails, continue with others
                    continue
                    
        except Exception as e:
            print(f"⚠️ Error in main loop: {e}")
        
        # Wait 30 seconds before checking again
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