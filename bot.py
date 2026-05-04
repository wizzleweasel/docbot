#!/usr/bin/env python3
"""
docbot - Telegram bot that chunks conversations into .txt files
for document support and context recall.
"""
import os
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import telebot
from telebot.types import Message
import time

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

# Session settings
SESSION_TIMEOUT = 120  # 2 minutes
MAX_MESSAGES = 100

if not BOT_TOKEN:
    print("ERROR: TELEGRAM_BOT_TOKEN not set in .env")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# Session storage: chat_id -> session data
sessions = {}

def clean_filename(text: str, max_len: int = 30) -> str:
    """Clean text for use in filename."""
    safe = "".join(c for c in text if c.isalnum() or c in (' ', '-', '_')).strip()
    safe = safe.replace(' ', '_')[:max_len]
    return safe or "unknown"

def get_sender_info(message: Message) -> dict:
    """Extract sender information from message."""
    if message.from_user:
        user = message.from_user
        return {
            'name': f"{user.first_name or ''} {user.last_name or ''}".strip(),
            'username': f"@{user.username}" if user.username else "",
            'id': user.id
        }
    return {'name': 'Unknown', 'username': '', 'id': 0}

def get_chat_info(message: Message) -> dict:
    """Extract chat information."""
    return {
        'title': message.chat.title or f"chat_{message.chat.id}",
        'id': message.chat.id,
        'type': message.chat.type
    }

class ConversationSession:
    """Tracks a conversation session for chunking."""
    
    def __init__(self, chat_id: int, chat_info: dict, sender_info: dict):
        self.chat_id = chat_id
        self.chat_info = chat_info
        self.sender_info = sender_info
        self.messages = []
        self.start_time = datetime.now()
        self.last_message_time = datetime.now()
        self.message_count = 0
        self.session_id = int(time.time())
        
    def add_message(self, message: Message):
        """Add a message to the session."""
        self.messages.append(message)
        self.last_message_time = datetime.now()
        self.message_count += 1
        
    def should_end(self) -> tuple:
        """Check if session should end. Returns (should_end, reason)."""
        # Check timeout
        inactive_time = (datetime.now() - self.last_message_time).total_seconds()
        if inactive_time >= SESSION_TIMEOUT:
            return True, f"timeout ({SESSION_TIMEOUT}s inactive)"
        
        # Check message count
        if self.message_count >= MAX_MESSAGES:
            return True, f"max messages ({MAX_MESSAGES})"
        
        return False, ""
    
    def save_to_file(self, reason: str = "session ended") -> Path:
        """Save the conversation chunk to a file."""
        if not self.messages:
            return None
        
        # Build filename
        timestamp = self.start_time.strftime('%Y%m%d_%H%M%S')
        chat_name = clean_filename(self.chat_info['title'])
        sender_name = clean_filename(self.sender_info['name'])
        filename = f"chunk_{timestamp}_{chat_name}_{sender_name}_{self.session_id}.txt"
        filepath = DOCS_DIR / filename
        
        # Build content
        duration = (self.last_message_time - self.start_time).total_seconds() / 60.0
        
        lines = [
            "=== Conversation Chunk ===",
            f"Session Start: {self.start_time.isoformat()}",
            f"Session End: {self.last_message_time.isoformat()}",
            f"User: {self.sender_info['name']} {self.sender_info['username']}",
            f"Chat: {self.chat_info['title']} (ID: {self.chat_info['id']}, Type: {self.chat_info['type']})",
            f"Total Messages: {self.message_count}",
            f"Duration: {duration:.1f} minutes",
            f"End Reason: {reason}",
            "",
            "=== Messages ==="
        ]
        
        # Add messages in chronological order (oldest first)
        for msg in self.messages:
            msg_time = datetime.fromtimestamp(msg.date).isoformat()
            sender = get_sender_info(msg)
            text = msg.text or msg.caption or ""
            
            # Handle media
            if not text and msg.document:
                text = f"[Document: {msg.document.file_name}]"
            elif not text and msg.photo:
                text = "[Photo]"
            elif not text and msg.voice:
                text = "[Voice Message]"
            elif not text:
                text = "[No text content]"
            
            lines.append(f"[{msg_time}] {sender['name']}: {text}")
        
        lines.append("")
        lines.append(f"=== End of chunk ({self.message_count} messages, {duration:.1f} minutes) ===")
        
        content = "\n".join(lines)
        filepath.write_text(content, encoding='utf-8')
        
        return filepath

def send_file_via_http(chat_id, filepath, caption):
    """Send file using direct HTTP API (more reliable than library)."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    with open(filepath, 'rb') as f:
        # Use tuple (filename, file_object, mime_type) to preserve original filename
        files_param = {'document': (filepath.name, f, 'text/plain')}
        data = {'chat_id': chat_id, 'caption': caption}
        resp = requests.post(url, files=files_param, data=data)
        if not resp.json().get('ok'):
            print(f"Error sending file: {resp.json().get('description')}")
    return resp.json().get('ok', False)

def get_or_create_session(message: Message) -> ConversationSession:
    """Get existing session or create new one."""
    chat_id = message.chat.id
    
    # Check if session exists and is still valid
    if chat_id in sessions:
        session = sessions[chat_id]
        should_end, reason = session.should_end()
        if should_end:
            # Save and remove old session
            filepath = session.save_to_file(reason)
            del sessions[chat_id]
            # Fall through to create new session
    
    # Create new session
    if chat_id not in sessions:
        chat_info = get_chat_info(message)
        sender_info = get_sender_info(message)
        sessions[chat_id] = ConversationSession(chat_id, chat_info, sender_info)
    
    return sessions[chat_id]

# Command handlers
@bot.message_handler(commands=['ping', 'test', 'start'])
def handle_ping(message: Message):
    """Respond to /ping, /test, /start commands."""
    bot.reply_to(message, "🏓 Pong! docbot is **LIVE** and ready to chunk your conversations!\n\n"
                          "Just send messages and I'll group them into `.txt` chunks.\n"
                          "Use `proceed` or `/proceed` to save the current chunk early.\n"
                          "Sessions auto-save after 2 min inactivity or 100 messages.")

@bot.message_handler(commands=['proceed'])
def handle_proceed(message: Message):
    """Explicitly end current session and save."""
    chat_id = message.chat.id
    if chat_id in sessions:
        session = sessions[chat_id]
        filepath = session.save_to_file("user sent /proceed")
        del sessions[chat_id]
        if filepath:
            bot.reply_to(message, f"✅ Chunk saved as `{filepath.name}`\n\nReady for new messages!")
            # Send file directly
            send_file_via_http(chat_id, filepath, f"📄 {filepath.name}")
        else:
            bot.reply_to(message, "⚠️ No messages to save in this session.")
    else:
        bot.reply_to(message, "ℹ️ No active session. Start sending messages!")

# Text handlers for proceed/cancel
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ['proceed', 'pong'])
def handle_text_proceed(message: Message):
    """Handle plain text 'proceed' or 'pong'."""
    if message.text.lower() == 'proceed':
        handle_proceed(message)
    else:
        bot.reply_to(message, "🏓 I'm alive! docbot is **LIVE** and chunking conversations!\n\n"
                              "Send messages and I'll group them into `.txt` chunks.\n"
                              "Use `proceed` to save early, or wait 2 min for auto-save.")

@bot.message_handler(func=lambda m: m.text and m.text.lower() == 'cancel')
def handle_cancel(message: Message):
    """Cancel current session without saving."""
    chat_id = message.chat.id
    if chat_id in sessions:
        del sessions[chat_id]
        bot.reply_to(message, "🗑️ Current session cancelled. No file saved.\n\nStart fresh!")
    else:
        bot.reply_to(message, "ℹ️ No active session to cancel.")

@bot.message_handler(commands=['list', 'files'])
def handle_list(message: Message):
    """List all saved chunks for this user/chat."""
    chat_id = message.chat.id
    
    # Get all chunk files for this chat - oldest first (newest at bottom)
    files = sorted(DOCS_DIR.glob(f"chunk_*_{chat_id}_*.txt"), key=os.path.getmtime, reverse=False)
    
    if not files:
        bot.reply_to(message, "📂 No saved chunks found for this chat.\n\nSend some messages and use `proceed` to save!")
        return
    
    # Build list (show last 10, which are the newest)
    lines = ["📄 **Saved chunks:** (oldest → newest)", ""]
    for i, f in enumerate(files[-10:], start=max(1, len(files)-9)):
        size_kb = f.stat().st_size / 1024
        lines.append(f"{i}. `{f.name}` ({size_kb:.1f} KB)")
    
    if len(files) > 10:
        lines.append(f"\n...and {len(files) - 10} older files")
    
    lines.append("\n💡 Send `/get <number>` to download (e.g., `/get 1` for oldest)")
    
    bot.reply_to(message, "\n".join(lines))

@bot.message_handler(commands=['get'])
def handle_get(message: Message):
    """Send a specific chunk file by number from /list."""
    chat_id = message.chat.id
    
    # Parse file number
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        bot.reply_to(message, "❌ Usage: `/get <number>`\nCheck `/list` for available files.")
        return
    
    idx = int(parts[1]) - 1  # Convert to 0-based
    
    # Get files
    files = sorted(DOCS_DIR.glob(f"chunk_*_{chat_id}_*.txt"), key=os.path.getmtime, reverse=True)
    
    if idx < 0 or idx >= len(files):
        bot.reply_to(message, f"❌ Invalid number. Use `/list` to see available files (1={oldest}, {len(files)}=newest).")
        return
    
    filepath = files[idx]
    # Send file using direct HTTP API
    send_file_via_http(chat_id, filepath, f"📄 {filepath.name}")

# Main message handler
@bot.message_handler(func=lambda m: True)
def handle_message(message: Message):
    """Handle all incoming messages."""
    try:
        text = message.text or message.caption or ""
        text_lower = text.lower().strip()
        
        # Skip command messages (already handled)
        if text.startswith('/'):
            return
        
        # Skip proceed/cancel (already handled)
        if text_lower in ['proceed', 'cancel', 'pong', 'ping', 'test', 'start']:
            return
        
        # Get or create session
        session = get_or_create_session(message)
        
        # Add message to session
        session.add_message(message)
        
        # Check if session should end now (after adding)
        should_end, reason = session.should_end()
        if should_end:
            filepath = session.save_to_file(reason)
            del sessions[message.chat.id]
            if filepath:
                bot.reply_to(message, f"✅ Chunk saved as `{filepath.name}` ({session.message_count} messages)\n\nReady for new messages!")
                # Send file directly
                send_file_via_http(message.chat.id, filepath, f"📄 {filepath.name}")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")
        print(f"Error: {e}")

if __name__ == '__main__':
    print(f"docbot starting... Saving to {DOCS_DIR}")
    print(f"Session settings: {SESSION_TIMEOUT}s timeout, {MAX_MESSAGES} max messages")
    try:
        bot_info = bot.get_me()
        print(f"✅ Connected as @{bot_info.username}")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        exit(1)
    
    print("Polling for messages...")
    bot.infinity_polling()
