import os
import threading
import sys
import time
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Crypto Bot is running on Railway!"

@app.route('/health')
def health():
    return "OK"

def run_bot():
    """Run the Telegram bot"""
    try:
        print("🤖 Starting Telegram bot...")
        os.system("python telegram_bot.py")
    except Exception as e:
        print(f"❌ Bot error: {e}")

# Start bot in background when app loads
print("🚀 Initializing bot...")
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()
print("✅ Bot thread started!")

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)