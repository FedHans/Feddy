import os
import sys
from flask import Flask, request, jsonify
import subprocess
import threading
import time

app = Flask(__name__)

# Get token from environment
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not set!")
    sys.exit(1)

@app.route('/')
def home():
    return "🤖 Crypto Bot is running on Railway!"

@app.route('/health')
def health():
    return "OK", 200

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    """Receive updates from Telegram"""
    try:
        # Forward the update to your bot
        import json
        update_data = request.get_json()
        
        # Process the update
        # You'll need to integrate your bot logic here
        process_update(update_data)
        
        return "OK", 200
    except Exception as e:
        print(f"Webhook error: {e}")
        return "Error", 500

def process_update(update_data):
    """Process incoming Telegram updates"""
    # This is where your bot logic goes
    print(f"Received update: {update_data}")

def run_polling():
    """Run the bot in polling mode as fallback"""
    time.sleep(10)  # Wait for webhook to be ready
    print("Starting polling mode...")
    os.system("python telegram_bot.py")

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    
    # Start polling in background (fallback)
    poll_thread = threading.Thread(target=run_polling, daemon=True)
    poll_thread.start()
    
    # Start web server
    app.run(host='0.0.0.0', port=port)