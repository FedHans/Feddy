import asyncio
from telegram import Bot
import sys
from fundamentals import get_coin_fundamentals

TOKEN = "8798845138:AAGVPd5K9_ItEdqyulLbXA9WpHTHzClTl4c"
CHAT_ID = "7245319588"

async def send_fundamentals(coin_name):
    bot = Bot(token=TOKEN)
    
    print(f"📊 Fetching fundamentals for {coin_name}...")
    
    result = get_coin_fundamentals(coin_name)
    
    # Send to Telegram
    await bot.send_message(chat_id=CHAT_ID, text=result)
    print(f"✅ Fundamentals for {coin_name} sent to Telegram!")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        coin = sys.argv[1]
        asyncio.run(send_fundamentals(coin))
    else:
        print("Usage: python send_fundamentals.py [coin_name]")
        print("Example: python send_fundamentals.py bitcoin")