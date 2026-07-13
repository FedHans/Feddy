#!/bin/bash
echo "🚀 Starting bot..."
python telegram_bot.py &
gunicorn app:app