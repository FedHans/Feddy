import os
import sys
import subprocess
import threading
import time

def run_bot():
    """Run the bot in the background"""
    print("🚀 Starting bot...")
    try:
        subprocess.run(["python", "telegram_bot.py"])
    except Exception as e:
        print(f"❌ Bot error: {e}")

if __name__ == "__main__":
    # Start bot in background
    import threading
    bot_thread = threading.Thread(target=run_bot, daemon=False)
    bot_thread.start()
    
    # Keep the process alive
    while True:
        time.sleep(60)