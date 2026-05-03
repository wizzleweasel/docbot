#!/usr/bin/env python3
"""
docbot - Simple Telegram bot that saves forwarded messages as .txt files
for document support and context recall.
"""
import os
import json
from datetime import datetime
from pathlib import Path
import telebot
from telebot.types import Message

# Load config from .env
def load_env():
    env_file = Path(__file__).parent / '.env'
    config = {}
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    return config

config = load_env()
BOT_TOKEN = config.get('TELEGRAM_BOT_TOKEN', '')
DOCS_DIR = Path('/home/runner/workspace/bot-docs')
DOCS_DIR.mkdir(parents=True, exist_ok=True)

if not BOT_TOKEN:
    print("ERROR: TELEGRAM_BOT_TOKEN not set in .env")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

def get_sender_info(message: Message) -> str:
    """Extract sender information from message."""
    if message.from_user:
        user = message.from_user
        name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        username = f"@{user.username}" if user.username else ""
        return f"{name} {username}".strip()
    return "Unknown"

def save_message_as_txt(message: Message, prefix: str = "msg") -> Path:
    """Save a message as a .txt file with metadata."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    sender = get_sender_info(message)
    chat_title = message.chat.title if message.chat.title else f"chat_{message.chat.id}"
    
    # Clean filename
    safe_sender = "".join(c for c in sender if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_sender = safe_sender.replace(' ', '_')[:30]
    safe_chat = "".join(c for c in chat_title if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_chat = safe_chat.replace(' ', '_')[:30]
    
    filename = f"{prefix}_{timestamp}_{safe_chat}_{safe_sender}.txt"
    filepath = DOCS_DIR / filename
    
    # Build content with metadata
    content_lines = [
        f"=== Message Metadata ===",
        f"Timestamp: {datetime.now().isoformat()}",
        f"Sender: {sender}",
        f"Chat: {chat_title} (ID: {message.chat.id})",
        f"Message ID: {message.message_id}",
    ]
    
    # Check if forwarded
    if message.forward_from or message.forward_from_chat:
        content_lines.append("=== Forwarded From ===")
        if message.forward_from:
            fwd_user = message.forward_from
            fwd_name = f"{fwd_user.first_name or ''} {fwd_user.last_name or ''}".strip()
            content_lines.append(f"User: {fwd_name} (@{fwd_user.username})" if fwd_user.username else f"User: {fwd_name}")
        if message.forward_from_chat:
            content_lines.append(f"Chat: {message.forward_from_chat.title} (ID: {message.forward_from_chat.id})")
        if message.forward_date:
            content_lines.append(f"Original Date: {datetime.fromtimestamp(message.forward_date).isoformat()}")
    
    content_lines.append("")
    content_lines.append("=== Message Content ===")
    
    # Get message text
    text = message.text or message.caption or ""
    if not text and message.document:
        text = f"[Document: {message.document.file_name}]"
    if not text and message.photo:
        text = "[Photo]"
    if not text and message.voice:
        text = "[Voice Message]"
    if not text:
        text = "[No text content]"
    
    content_lines.append(text)
    
    content = "\n".join(content_lines)
    filepath.write_text(content, encoding='utf-8')
    
    return filepath

@bot.message_handler(func=lambda m: True)
def handle_message(message: Message):
    """Handle all incoming messages."""
    try:
        # Save the message
        filepath = save_message_as_txt(message, prefix="msg")
        
        # Reply with confirmation
        rel_path = str(filepath.relative_to(DOCS_DIR))
        bot.reply_to(message, f"✅ Saved as `{rel_path}`\n\nUse this file for context recall with Cumi!")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error saving message: {str(e)}")
        print(f"Error: {e}")

if __name__ == '__main__':
    print(f"docbot starting... Saving to {DOCS_DIR}")
    print(f"Bot username will be shown after connecting...")
    try:
        bot_info = bot.get_me()
        print(f"✅ Connected as @{bot_info.username}")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        exit(1)
    
    print("Polling for messages...")
    bot.infinity_polling()
