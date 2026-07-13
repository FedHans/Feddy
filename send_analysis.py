import asyncio
from telegram import Bot
from technical_analysis import generate_portfolio_report

TOKEN = "8798845138:AAGVPd5K9_ItEdqyulLbXA9WpHTHzClTl4c"
CHAT_ID = "7245319588"

async def send_analysis():
    bot = Bot(token=TOKEN)
    
    await bot.send_message(chat_id=CHAT_ID, text="📊 Generating portfolio analysis... Please wait...")
    
    print("📊 Generating portfolio analysis...")
    report = generate_portfolio_report()
    
    # Send in chunks if too long
    if len(report) > 4096:
        for i in range(0, len(report), 4096):
            await bot.send_message(chat_id=CHAT_ID, text=report[i:i+4096])
            await asyncio.sleep(0.5)
    else:
        await bot.send_message(chat_id=CHAT_ID, text=report)
    
    print("✅ Portfolio analysis sent to Telegram!")

if __name__ == "__main__":
    asyncio.run(send_analysis())