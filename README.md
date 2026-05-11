# Personal AI Assistant — Telegram Bot

A personal AI assistant in Telegram powered by Google Gemini. Answers questions, remembers conversation context, and searches your facilitation knowledge base. Hosted on Render — free, 24/7.

## What it does

- **Chat:** Ask anything — the bot responds in the same language you write in
- **Smart model switching:** casual questions use Gemini Flash (fast), deep analysis uses Gemini Pro (just say "think deeply" or "порассуждай")
- **Knowledge base:** Searches your facilitation wiki (GitHub) and injects relevant pages into context automatically
- **Conversation memory:** Remembers the last 10 messages within a session
- **Single-user:** Only responds to your Telegram account

## Message examples

```
You: What technique should I use for a group of 40 people making a fast decision?
Bot: [searches knowledge base → loads relevant wiki pages → answers with specific techniques]

You: подумай детально про ризики цього підходу
Bot: [switches to Pro model → deeper analysis]

You: /clear
Bot: Context cleared.
```

---

## Setup Instructions

### Step 1 — Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Enter a name and username for your bot
4. Save the token — looks like `123456789:ABCdef...`

### Step 2 — Get your Telegram User ID

1. Open Telegram and search for **@userinfobot**
2. Send any message to it
3. It replies with your numeric user ID — save it (e.g. `123456789`)

This ID is used to restrict the bot so only you can use it.

### Step 3 — Get a Google AI API Key (free)

1. Go to **aistudio.google.com**
2. Sign in with your Google account
3. Click **Get API key** → **Create API key in new project**
4. Save the key — starts with `AIza...`

> **Important:** Create the key in a **new project** to get a fresh free quota.
> Free tier: 1,500 requests/day for Gemini Flash — more than enough for personal use.

### Step 4 — Deploy to Render (free hosting)

1. Fork this repo to your GitHub account
2. Go to **render.com** and sign up (free, GitHub login works)
3. Click **New → Web Service**
4. Connect your GitHub account and select your forked repo
5. Set **Runtime** to **Docker**
6. Click **Create Web Service** — note the URL it gives you (e.g. `https://my-assistant-xyz.onrender.com`)

### Step 5 — Add Environment Variables

In Render: **Environment → Add variable** (add all 4):

| Variable | Value | Where to get it |
|----------|-------|----------------|
| `TELEGRAM_BOT_TOKEN` | `123456:ABC...` | Step 1 — BotFather |
| `GOOGLE_API_KEY` | `AIza...` | Step 3 — AI Studio |
| `WEBHOOK_BASE_URL` | `https://your-app.onrender.com` | Step 4 — Render URL |
| `ALLOWED_USER_ID` | `123456789` | Step 2 — userinfobot |

Click **Save, rebuild, and deploy**.

### Step 6 — Test it

1. Open Telegram and find your bot
2. Send `/start`
3. Ask it anything

> **Note on cold starts:** Render free tier sleeps after 15 minutes of inactivity. The first message after a sleep takes ~30-50 seconds. Subsequent messages are fast.

---

## Commands

| Command | What it does |
|---------|-------------|
| `/start` | Welcome message |
| `/clear` | Clear conversation context |

## Trigger deep thinking mode

Add any of these to your message to switch to Gemini Pro:

- `подумай`, `порассуждай`, `розмірковуй`
- `think deeply`, `reason`, `think harder`
- `детально`, `подробно`, `глибоко`

---

## Knowledge Base

The bot searches a public GitHub repo (`telegram-ai-knowledge`) for relevant knowledge before answering. Currently contains a facilitation wiki (14 pages, 60+ techniques).

**Two-phase navigation:**
1. Bot reads `wiki/index.md` → Gemini selects relevant pages
2. Bot loads those pages → Gemini answers with that context

To add your own knowledge: edit the `telegram-ai-knowledge` repo and add markdown files with a one-line description in `wiki/index.md`.

---

## Architecture

```
app/
  main.py           ← FastAPI app + Telegram webhook registration
  bot.py            ← aiogram message handlers (/start, /clear, messages)
  llm.py            ← Gemini client with Flash/Pro switching
  memory.py         ← In-memory conversation history (last 10 messages)
  knowledge.py      ← GitHub knowledge base navigator (two-phase retrieval)
Dockerfile          ← Python 3.12 container
render.yaml         ← Render deployment config
```

## Stack

- **Bot framework:** aiogram v3 (webhook mode)
- **Web server:** FastAPI + uvicorn
- **LLM:** Google Gemini 2.5 Flash / Pro
- **Knowledge base:** Public GitHub repo (raw file access, no auth needed)
- **Hosting:** Render (free tier, Docker)
- **Cost:** $0/month
