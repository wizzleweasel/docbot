# 📄 docbot

> *"Ugh. Me save message. You read later. Simple."* — docbot, probably

A **dead-simple Telegram bot** that catches forwarded messages and saves them as `.txt` files for **document support & context recall**. No databases, no APIs, no bloat — just pure file-based memory for your AI agents.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-2CA5E0?logo=telegram)](https://core.telegram.org/bots)

---

## 🔥 Why docbot?

| **Before docbot** | **After docbot** |
|-------------------|------------------|
| Forward message, forget context | Forward message, **saved as `.txt`** |
| AI agent has no long-term memory | AI agent reads files, **remembers everything** |
| Copy-paste into chat manually | **Automatic document support** |
| Context gets lost in noise | Clean `.txt` chunks, **searchable & reusable** |

---

## 🚀 Quick Start

### 1. Get a Bot Token
Message [@BotFather](https://t.me/BotFather) on Telegram:
```
/newbot
Name: docbot
Username: your_docbot_bot
```
Copy the token he gives you.

### 2. Configure
```bash
git clone https://github.com/wizzleweasel/docbot.git
cd docbot
cp .env.example .env  # or edit .env directly
```
Paste your token in `.env`:
```env
TELEGRAM_BOT_TOKEN=your_token_here
```

### 3. Run
```bash
./start.sh
```
Bot says: `✅ Connected as @your_docbot_bot`

### 4. Use It
- Forward any message to your bot
- Bot replies: `✅ Saved as msg_20260503_193000_chat_sender.txt`
- **Cumi (or any AI agent) can now read that file for context!**

---

## 📁 How It Works

```
User forwards message → docbot → saves as .txt in /bot-docs/
                                  └─ Your AI Agent reads file → better context recall
```

**File format:**
```
=== Message Metadata ===
Timestamp: 2026-05-03T19:30:00
Sender: John Doe @johndoe
Chat: MyGroup (ID: -100123456)
=== Forwarded From ===
User: Alice @alice
Original Date: 2026-05-01T10:00:00

=== Message Content ===
(actual message text here)
```

---

## 🛠️ Features

- ✅ **Saves forwarded messages** as searchable `.txt` files
- ✅ **Metadata included** — sender, chat, timestamps, forward info
- ✅ **Open access** — anyone can use it (no chat restrictions)
- ✅ **AI-agent friendly** — Your AI Agent can `read_file` or `search_files` to recall context
- ✅ **Zero bloat** — no databases, no APIs, just files
- ✅ **Lightweight** — runs on a potato

---

## 📦 Requirements

- Python 3.8+
- `pyTelegramBotAPI` (auto-installed by `start.sh`)
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

---


## 📜 License

MIT — do whatever you want with it. Just don't blame me if it eats your messages.

---

## 🗿 Caveman Slogan

> *"Me save. You read. Context good."*

---

**Built with ❤️ by [wizzleweasel](https://github.com/wizzleweasel) as part of our development journey.**
