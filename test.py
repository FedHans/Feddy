import asyncio
from telegram import Bot

# ✅ YES - quotes around the token
TOKEN = "8798845138:AAGVPd5K9_ItEdqyulLbXA9WpHTHzClTl4c"
CHAT_ID = "7245319588"

async def send_test():
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text="✅ Test message from Python!")
    print("✅ Message sent!")

if __name__ == "__main__":
    asyncio.run(send_test())