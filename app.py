import os
import threading
import sys
from flask import Flask

# Add the current directory to path so Python can find your files
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Crypto Bot is running on Railway!"

@app.route('/health')
def health():
    return "OK"

def run_bot():
    try:
        os.system("python telegram_bot.py")
    except Exception as e:
        print(f"Error running bot: {e}")

if __name__ == "__main__":
    # Start the bot in a background thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    print("🤖 Bot thread started!")
    
    # Start the web server
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting web server on port {port}...")
    app.run(host='0.0.0.0', port=port)