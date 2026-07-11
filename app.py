import os
import threading
import time
from flask import Flask
import subprocess

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Crypto News Bot is running!"

@app.route('/health')
def health():
    return "OK"

def run_news_bot():
    """Run the news alert script in a separate thread"""
    os.system("python news_alert.py")

def run_daily_report():
    """Run the daily report script"""
    os.system("python send_full_report.py")

# Start the news bot in a background thread
if __name__ == "__main__":
    # Run news alerts in background
    thread = threading.Thread(target=run_news_bot)
    thread.daemon = True
    thread.start()
    
    # Also run a daily report when the app starts
    run_daily_report()
    
    # Keep the web server running
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)