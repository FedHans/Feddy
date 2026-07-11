import asyncio
from telegram import Bot
import requests
from datetime import datetime, timedelta
import feedparser

TOKEN = "8798845138:AAGVPd5K9_ItEdqyulLbXA9WpHTHzClTl4c"
CHAT_ID = "7245319588"

def get_daily_change(coin_id):
    """Get the daily change from today's open (00:00 UTC)"""
    try:
        # Get current price
        price_response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": coin_id, "vs_currencies": "usd"}
        )
        current_price = price_response.json()[coin_id]["usd"]
        
        # Get the start of today (00:00 UTC) as a date string
        today = datetime.now().strftime("%d-%m-%Y")
        
        # Get historical data for today
        hist_response = requests.get(
            f"https://api.coingecko.com/api/v3/coins/{coin_id}/history",
            params={
                "date": today,
                "localization": "false"
            }
        )
        hist_data = hist_response.json()
        
        # Get today's open price (first price of the day)
        # The history endpoint returns market_data with current_price
        if "market_data" in hist_data and "current_price" in hist_data["market_data"]:
            open_price = hist_data["market_data"]["current_price"]["usd"]
            # Sometimes the historical data is not the exact open price, but it's the best we have
            change = ((current_price - open_price) / open_price) * 100
            return current_price, change
        else:
            return current_price, 0
            
    except Exception as e:
        print(f"⚠️ Error getting {coin_id} daily change: {e}")
        return "N/A", 0

async def send_report():
    bot = Bot(token=TOKEN)
    
    print("📊 Fetching market data and news...")
    
    # 1. Fetch Fear & Greed Index
    try:
        fng_response = requests.get("https://api.alternative.me/fng/")
        fng_data = fng_response.json()
        fng_value = fng_data["data"][0]["value"]
        fng_sentiment = fng_data["data"][0]["value_classification"]
    except:
        fng_value = "N/A"
        fng_sentiment = "N/A"
    
    # 2. Get Bitcoin daily change
    btc_price, btc_change = get_daily_change("bitcoin")
    btc_change_symbol = "🟢" if btc_change > 0 else "🔴" if btc_change < 0 else "⚪"
    
    # 3. Get Ethereum daily change
    eth_price, eth_change = get_daily_change("ethereum")
    eth_change_symbol = "🟢" if eth_change > 0 else "🔴" if eth_change < 0 else "⚪"
    
    # 4. Fetch Crypto News from RSS Feeds
    news_list = []
    
    rss_feeds = [
        {"url": "https://cointelegraph.com/rss", "name": "CoinTelegraph"},
        {"url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "name": "CoinDesk"},
        {"url": "https://bitcoinmagazine.com/.rss", "name": "Bitcoin Magazine"},
        {"url": "https://decrypt.co/feed", "name": "Decrypt"}
    ]
    
    for feed_source in rss_feeds:
        try:
            feed = feedparser.parse(feed_source["url"])
            for entry in feed.entries[:5]:
                title = entry.title
                if len(title) > 120:
                    title = title[:117] + "..."
                
                pub_date = "Unknown"
                if hasattr(entry, 'published'):
                    pub_date = entry.published[:16] if len(entry.published) > 16 else entry.published
                
                summary = ""
                if hasattr(entry, 'summary'):
                    summary = entry.summary[:150] + "..." if len(entry.summary) > 150 else entry.summary
                elif hasattr(entry, 'description'):
                    summary = entry.description[:150] + "..." if len(entry.description) > 150 else entry.description
                
                link = entry.link if hasattr(entry, 'link') else ""
                
                news_list.append({
                    "title": title,
                    "source": feed_source["name"],
                    "date": pub_date,
                    "summary": summary,
                    "link": link
                })
        except Exception as e:
            continue
    
    # 5. Build report
    report = f"""
============================================================
  📊 Daily Crypto Market Briefing + News
  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
============================================================

📈 **CRYPTO PRICES** (Daily Change from today's open)
  Bitcoin (BTC): ${btc_price:,.2f} {btc_change_symbol} {btc_change:+.2f}%
  Ethereum (ETH): ${eth_price:,.2f} {eth_change_symbol} {eth_change:+.2f}%

😨 **FEAR & GREED INDEX**
  Value: {fng_value} ({fng_sentiment})

📊 **MARKET SENTIMENT**
  Market is currently {fng_sentiment.lower()}.

============================================================
📰 **LATEST CRYPTO NEWS** (with market impact analysis)
============================================================

"""
    
    if news_list:
        for i, item in enumerate(news_list[:10], 1):
            title_lower = item["title"].lower()
            
            bullish_strong = ["surge", "rally", "moon", "all-time high", "ath", "breakthrough", "approval", "inflow record"]
            bearish_strong = ["crash", "disaster", "wipeout", "catastrophe", "crisis", "bankruptcy"]
            bullish = ["gain", "bullish", "approval", "inflow", "adoption", "partnership", "green", "growth", "positive"]
            bearish = ["decline", "bearish", "reject", "ban", "restrict", "fine", "investigate", "drops", "plunge"]
            
            if any(word in title_lower for word in bullish_strong):
                impact = "🟢 Strongly Bullish"
            elif any(word in title_lower for word in bearish_strong):
                impact = "🔴 Strongly Bearish"
            elif any(word in title_lower for word in bullish):
                impact = "🟢 Bullish"
            elif any(word in title_lower for word in bearish):
                impact = "🔴 Bearish"
            else:
                impact = "⚪ Neutral"
            
            snippet = item["summary"][:100] + "..." if len(item["summary"]) > 100 else item["summary"]
            
            report += f"""
{i}. {item['title']}
   📰 {item['source']} @ {item['date']}
   📊 Impact: {impact}
   💡 {snippet}
"""
    else:
        report += "No news available at this time. Please try again later."
    
    report += f"""

============================================================
  Sources:
  📊 Fear & Greed: alternative.me
  💰 Prices: CoinGecko (daily change from today's open at 00:00 UTC)
  📰 News: CoinTelegraph, CoinDesk, Bitcoin Magazine, Decrypt
  🔒 No API keys required - 100% free
  Data refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
============================================================
"""
    
    print(f"Report size: {len(report)} characters")
    
    await bot.send_message(chat_id=CHAT_ID, text=report)
    print("✅ Report sent to Telegram!")

if __name__ == "__main__":
    asyncio.run(send_report())