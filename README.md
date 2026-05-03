# docbot 📄

> *"me save message. you read later. simple."* — docbot

A minimal Telegram bot that saves forwarded messages as `.txt` files for document support and context recall. No AI, no fancy features — just saves your messages so **cumi** (Hermes Agent) can read them later.

---

## 🔥 What It Does

| Before | After |
|--------|-------|
| Messages get lost in Telegram history | Messages saved as searchable `.txt` files |
| Can't give cumi good context | Point cumi at `bot-docs/` folder |
| Forwarding = manual copy-paste | Forward → auto-saved with metadata |

---

## 🚀 Quick Start

### 1. Get a Bot Token
Message [@BotFather](https://t.me/BotFather) on Telegram:
```
/newbot
docbot
```
Copy the token he gives you.

### 2. Configure
```bash
cd /home/runner/workspace/doc-bot
# Edit .env and add your token:
echo "TELEGRAM_BOT_TOKEN=your_token_here" > .env
```

### 3. Run
```bash
./start.sh
```

### 4. Use It
- Forward any message to your bot on Telegram
- Bot replies with the filename
- Files saved to `/home/runner/workspace/bot-docs/`
- Tell **cumi**: *"check bot-docs/ for context about X"*

---

## 📄 File Format

Saved files look like:
```
=== Message Metadata ===
Timestamp: 2026-05-03T19:30:00
Sender: John Doe @johndoe
Chat: MyGroup (ID: -100123456)
Message ID: 42
=== Forwarded From ===
User: Alice @alice
Original Date: 2026-05-01T10:00:00

=== Message Content ===
(actual message text here)
```

---

## 🛠️ Tech Stack

- **Language:** Python 3
- **Library:** pyTelegramBotAPI
- **Storage:** Plain `.txt` files (no database needed)
- **Hosting:** Runs on same system as cumi (Hermes Agent)

---

## 🤖 Integration with cumi

Once messages are saved, cumi can:
```python
# Search for relevant docs
search_files(pattern="keyword", path="/home/runner/workspace/bot-docs")

# Read specific file
read_file("/home/runner/workspace/bot-docs/msg_20260503_193000.txt")
```

---

## ⚠️ Caveats

- **Open access:** Bot accepts messages from any chat (set `ALLOWED_CHAT_IDS` in `.env` to restrict)
- **No encryption:** Files saved as plain text
- **No AI:** This bot just saves files, it doesn't understand them (that's cumi's job)

---

## 📊 Stats

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![Status](https://img.shields.io/badge/status-ready-success.svg)

---

**Built for the [Hermes Agent](https://github.com/NousResearch/hermes-agent) ecosystem.**  
*Part of the caveman/pierced-tongue/throw-rock family.* 🪨
