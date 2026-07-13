import os
import sys
import subprocess
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Crypto Bot is running on Railway!"

@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    # Start the bot using subprocess
    print("🚀 Starting bot...")
    subprocess.Popen(["python", "telegram_bot.py"])
    print("✅ Bot process started!")
    
    # Start web server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)