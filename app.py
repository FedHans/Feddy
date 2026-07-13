import os
import sys
import subprocess
import threading
import time
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Crypto Bot is running on Railway!"

@app.route('/health')
def health():
    return "OK", 200

def run_bot():
    """Run the bot with full output"""
    try:
        print("🚀 Starting bot process...")
        # Use python with unbuffered output
        result = subprocess.run(
            ["python", "-u", "telegram_bot.py"],
            capture_output=False,
            text=True
        )
        print(f"Bot process finished with code: {result}")
    except Exception as e:
        print(f"❌ Bot error: {e}")

if __name__ == "__main__":
    print("🚀 Initializing app...")
    
    # Start bot in a separate thread
    bot_thread = threading.Thread(target=run_bot, daemon=False)
    bot_thread.start()
    print("✅ Bot thread started!")
    
    # Start web server
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting web server on port {port}...")
    app.run(host='0.0.0.0', port=port)