#!/bin/bash
# Start docbot - Telegram document support bot
cd "$(dirname "$0")"

# Check if token is set
if ! grep -q "TELEGRAM_BOT_TOKEN=.*[^[:space:]]" .env 2>/dev/null; then
    echo "❌ TELEGRAM_BOT_TOKEN not set in .env"
    echo "   Get a token from @BotFather and add it to .env"
    exit 1
fi

# Create venv if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install pyTelegramBotAPI > /dev/null 2>&1
else
    source venv/bin/activate
fi

echo "Starting docbot..."
python3 bot.py
