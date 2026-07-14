import os
import asyncio
import time
import schedule
import requests
import feedparser
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from technical_analysis import generate_portfolio_report

# ============================================================
# CONFIGURATION
# ============================================================
# Get token from environment variable (Railway) or use hardcoded as fallback
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8798845138:AAGVPd5K9_ItEdqyulLbXA9WpHTHzClTl4c")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "7245319588")

# Check if running on Railway
IS_RAILWAY = os.environ.get('RAILWAY_ENVIRONMENT') is not None

# ============================================================
# FUNDAMENTALS FUNCTION
# ============================================================
def get_coin_fundamentals(coin_name):
    try:
        # Search for the coin ID first
        search_response = requests.get(
            f"https://api.coingecko.com/api/v3/search",
            params={"query": coin_name}
        )
        search_data = search_response.json()
        
        if not search_data.get("coins"):
            return f"❌ Coin '{coin_name}' not found. Please check the name."
        
        coin_id = search_data["coins"][0]["id"]
        coin_name_from_api = search_data["coins"][0]["name"]
        coin_symbol = search_data["coins"][0]["symbol"]
        
        response = requests.get(
            f"https://api.coingecko.com/api/v3/coins/{coin_id}",
            params={
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "true",
                "developer_data": "false",
                "sparkline": "false"
            }
        )
        data = response.json()
        market_data = data.get("market_data", {})
        
        # Check if market_data exists
        if not market_data:
            return f"❌ No market data available for '{coin_name}'"
        
        # Price
        current_price = market_data.get('current_price', {}).get('usd', 0)
        
        # Price changes
        price_change_24h = market_data.get('price_change_percentage_24h', 0)
        price_change_7d = market_data.get('price_change_percentage_7d', 0)
        price_change_30d = market_data.get('price_change_percentage_30d', 0)
        
        # Market cap
        market_cap = market_data.get('market_cap', {}).get('usd', 0)
        fdv = market_data.get('fully_diluted_valuation', {}).get('usd', 0)
        
        # Supply
        circulating_supply = market_data.get('circulating_supply', 0)
        total_supply = market_data.get('total_supply', 0)
        max_supply = market_data.get('max_supply', 0)
        
        # Format supply values
        if total_supply is None or total_supply == 0:
            total_supply_str = "Unlimited"
        else:
            total_supply_str = f"{total_supply:,.0f}"
        
        if max_supply is None or max_supply == 0:
            max_supply_str = "Unlimited"
        else:
            max_supply_str = f"{max_supply:,.0f}"
        
        # Trend analysis
        if price_change_24h > 5 and price_change_7d > 5:
            trend = "🟢 Strongly Bullish"
        elif price_change_24h > 2 and price_change_7d > 2:
            trend = "🟢 Bullish"
        elif price_change_24h < -5 and price_change_7d < -5:
            trend = "🔴 Strongly Bearish"
        elif price_change_24h < -2 and price_change_7d < -2:
            trend = "🔴 Bearish"
        elif price_change_24h > 0:
            trend = "🟡 Slightly Bullish"
        elif price_change_24h < 0:
            trend = "🟡 Slightly Bearish"
        else:
            trend = "⚪ Neutral"
        
        # Dilution analysis
        dilution_ratio = 0
        dilution_risk = "N/A"
        if market_cap > 0 and fdv > 0:
            dilution_ratio = fdv / market_cap
            if dilution_ratio > 3:
                dilution_risk = "🔴 High (FDV > 3x Market Cap)"
            elif dilution_ratio > 1.5:
                dilution_risk = "🟡 Medium (FDV 1.5-3x Market Cap)"
            else:
                dilution_risk = "🟢 Low (FDV < 1.5x Market Cap)"
        
        # Build the report
        report = f"""
📊 **{coin_name_from_api.upper()} ({coin_symbol.upper()})** - Fundamentals

💰 **Price & Market Data**
  Price: ${current_price:,.2f}
  Market Cap: ${market_cap:,.0f}
  FDV: ${fdv:,.0f}
  Rank: #{data.get('market_cap_rank', 'N/A')}

📦 **Supply & Tokenomics**
  Circulating: {circulating_supply:,.0f}
  Total: {total_supply_str}
  Max: {max_supply_str}

🔄 **Dilution Analysis**
  FDV / Market Cap: {dilution_ratio:.2f}x
  Risk: {dilution_risk}

📈 **Price Trend**
  24h: {price_change_24h:+.2f}%
  7d: {price_change_7d:+.2f}%
  30d: {price_change_30d:+.2f}%
  Overall: {trend}

💡 {coin_name_from_api} is trading at ${current_price:,.2f} with {circulating_supply:,.0f} tokens in circulation. {'Bullish momentum' if price_change_24h > 0 else 'Bearish pressure'} over the last 24 hours.

_Data: CoinGecko | DYOR_
"""
        return report
        
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ============================================================
# DAILY REPORT FUNCTION
# ============================================================
def get_daily_report():
    try:
        # Get BTC and ETH prices
        btc_response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin,ethereum", "vs_currencies": "usd", "include_24hr_change": "true"}
        )
        prices = btc_response.json()
        
        btc_price = prices.get("bitcoin", {}).get("usd", "N/A")
        btc_change = prices.get("bitcoin", {}).get("usd_24h_change", 0)
        eth_price = prices.get("ethereum", {}).get("usd", "N/A")
        eth_change = prices.get("ethereum", {}).get("usd_24h_change", 0)
        
        # Get Fear & Greed
        fng_response = requests.get("https://api.alternative.me/fng/")
        fng_data = fng_response.json()
        fng_value = fng_data["data"][0]["value"]
        fng_sentiment = fng_data["data"][0]["value_classification"]
        
        report = f"""
📊 **Daily Market Briefing**
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📈 **Prices**
  BTC: ${btc_price:,.2f} ({btc_change:+.2f}%)
  ETH: ${eth_price:,.2f} ({eth_change:+.2f}%)

😨 **Fear & Greed**
  {fng_value} - {fng_sentiment}

📰 **Top News**
"""
        # Get news from RSS
        try:
            feed = feedparser.parse("https://cointelegraph.com/rss")
            for entry in feed.entries[:5]:
                report += f"  • {entry.title}\n"
        except:
            report += "  • News temporarily unavailable\n"
        
        return report
    except Exception as e:
        return f"📊 Daily report temporarily unavailable: {str(e)}"

# ============================================================
# SCHEDULED TASKS
# ============================================================
async def send_portfolio_report():
    """Send portfolio report to Telegram"""
    try:
        bot = Bot(token=TOKEN)
        report = generate_portfolio_report()
        
        if len(report) > 4096:
            for i in range(0, len(report), 4096):
                await bot.send_message(chat_id=CHAT_ID, text=report[i:i+4096])
                await asyncio.sleep(0.5)
        else:
            await bot.send_message(chat_id=CHAT_ID, text=report)
        print("✅ Daily portfolio report sent!")
    except Exception as e:
        print(f"❌ Error sending portfolio report: {e}")

async def send_daily_report():
    """Send daily market briefing"""
    try:
        bot = Bot(token=TOKEN)
        report = get_daily_report()
        await bot.send_message(chat_id=CHAT_ID, text=report)
        print("✅ Daily market briefing sent!")
    except Exception as e:
        print(f"❌ Error sending daily report: {e}")

def schedule_daily_tasks():
    """Schedule daily tasks"""
    # Schedule portfolio report at 8:00 AM
    schedule.every().day.at("08:00").do(
        lambda: asyncio.create_task(send_portfolio_report())
    )
    # Schedule daily briefing at 8:30 AM
    schedule.every().day.at("08:30").do(
        lambda: asyncio.create_task(send_daily_report())
    )
    print("📅 Daily tasks scheduled: 8:00 AM (Portfolio), 8:30 AM (Briefing)")

# ============================================================
# TELEGRAM COMMANDS
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **Hello! I'm your Crypto Assistant!**\n\n"
        "**Commands:**\n"
        "/fundamentals [coin] - Get tokenomics & market data\n"
        "/daily - Get daily market briefing\n"
        "/portfolio - Get technical analysis & signals\n"
        "/help - Show this menu\n\n"
        "**Example:** /fundamentals bitcoin"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 **Available Commands:**\n\n"
        "/fundamentals [coin] - Analyze any coin's fundamentals\n"
        "/daily - Get daily market briefing\n"
        "/portfolio - Get technical analysis & buy/sell signals\n"
        "/start - Welcome message\n"
        "/help - This menu\n\n"
        "**Example:** /fundamentals solana"
    )

async def fundamentals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Please specify a coin.\n\nExample: /fundamentals bitcoin")
        return
    
    coin_name = " ".join(context.args)
    await update.message.reply_text(f"📊 Analyzing **{coin_name}**... Please wait...")
    
    result = get_coin_fundamentals(coin_name)
    await update.message.reply_text(result)

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Fetching daily briefing...")
    report = get_daily_report()
    await update.message.reply_text(report)

async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Generating portfolio analysis... Please wait...")
    
    report = generate_portfolio_report()
    
    if len(report) > 4096:
        for i in range(0, len(report), 4096):
            await update.message.reply_text(report[i:i+4096])
            await asyncio.sleep(0.5)
    else:
        await update.message.reply_text(report)

# ============================================================
# MAIN FUNCTION
# ============================================================
def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("fundamentals", fundamentals))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("portfolio", portfolio))
    
    print("🤖 Crypto Bot is starting...")
    print(f"📱 Running on: {'Railway' if IS_RAILWAY else 'Local'}")
    print("Commands: /start, /help, /fundamentals [coin], /daily, /portfolio")
    
    # Schedule daily tasks
    schedule_daily_tasks()
    
    # Start a background thread for the scheduler
    import threading
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("🔄 Scheduler started - will run tasks at scheduled times")
    
    print("🔄 Starting polling mode...")
    app.run_polling(allowed_updates=[])

if __name__ == "__main__":
    main()