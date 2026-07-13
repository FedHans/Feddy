import os
import threading
from flask import Flask
import subprocess

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Crypto Bot is running on Railway!"

@app.route('/health')
def health():
    return "OK"

def run_bot():
    """Run the Telegram bot"""
    os.system("python telegram_bot.py")

if __name__ == "__main__":
    # Start the bot in a background thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Start the web server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)