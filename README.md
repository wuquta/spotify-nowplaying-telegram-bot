
# Telegram Spotify Now Playing Bot 🎧

Telegram inline bot + backend that shows your **currently playing Spotify track** as a nice card in any chat.

- One-time Spotify connect via OAuth
- Type `@your_bot_username` in any chat
- Share what you are listening to right now

> Built as a small backend project: FastAPI + async SQLAlchemy + python-telegram-bot.

---

## How it works

1. You start a private chat with the bot and run `/connect`.
2. The bot asks the backend for a Spotify login link.
3. You authorize the app on Spotify. The backend stores your tokens in SQLite.
4. In any chat, you type `@your_bot_username` and pick a result.
5. The bot calls the backend `/api/now-playing`, which:
   - looks up your Spotify tokens,
   - calls Spotify **Get Currently Playing Track** API,
   - returns normalized track info (name, artists, album, cover, URL).
6. The bot sends a formatted “Now playing on Spotify” message into the chat.

No chat history or track data is stored permanently — only the tokens needed to talk to Spotify.

---

## Tech stack

- **Python 3.11+**
- **FastAPI** – backend API
- **python-telegram-bot 22.x** – Telegram bot (async, inline mode)
- **SQLAlchemy 2 (async)** + **SQLite** – user storage
- **httpx** – HTTP client for Spotify + backend calls
- **python-dotenv** – local env configuration

---

## Setup

### 1. Clone & create virtualenv

git clone https://github.com/YOUR_USERNAME/now-playing-bot.git
cd now-playing-bot

python -m venv .venv
source .venv/bin/activate # Windows: .venv\Scripts\activate

text

### 2. Install dependencies

pip install -r requirements.txt

text

(или `pip freeze > requirements.txt`, если используешь другой менеджер пакетов.)

### 3. Create a Telegram bot

1. Talk to **@BotFather**.
2. Run `/newbot` and follow the steps.
3. Copy the bot token.
4. Enable **inline mode**:
   - `/setinline` → choose your bot → set a placeholder like “Share Spotify track…”.

### 4. Create a Spotify app

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
2. Create a new app.
3. In app settings, add a **Redirect URI**:

http://127.0.0.1:8000/auth/callback

text

4. Copy **Client ID** and **Client Secret**.

### 5. Configure `.env`

Create a local `.env` from the example:

cp .env.example .env

text

Fill it with your values:

TELEGRAM_BOT_TOKEN=your_telegram_bot_token

SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/auth/callback

DATABASE_URL=sqlite+aiosqlite:///./data.db

text

---

## Running locally

### 1. Start the backend (FastAPI)

uvicorn app.main:app --reload

text

Healthcheck:

- `GET http://127.0.0.1:8000/health` → `{"status": "ok"}`

### 2. Start the Telegram bot

In another terminal (with the same virtualenv):

python -m bot.bot_main

text

---

## Usage

1. Open a private chat with your bot.
2. Run:

   - `/start` – short introduction
   - `/connect` – get a Spotify login link
   - authorize the app in browser
   - `/status` – check if Spotify is linked

3. Play any track in Spotify.
4. In **any chat** (private or group), type:

@your_bot_username

text

5. Choose the inline result “Share Spotify now playing”.

The bot will send a message like:

🎧 Now playing on Spotify:
Track Name by Artist
Album: Album Name
https://open.spotify.com/track/...

text

---

## Project structure

app/
main.py # FastAPI app, routers wiring, startup DB init
config.py # settings from .env
db.py # async SQLAlchemy engine/session
models.py # User model (Telegram + Spotify tokens)
spotify_client.py # OAuth and Spotify Web API helpers
routers/
auth.py # /auth/login, /auth/status, /auth/callback
now_playing.py # /api/now-playing

bot/
bot_main.py # Telegram bot: /start, /status, /connect, inline handler

.env.example # sample configuration
requirements.txt
README.md

text

---

## Possible improvements

- Refresh expired Spotify access tokens using `refresh_token`.
- Support “recently played” tracks and multiple inline options.
- Add a small web UI to show your current track.
- Dockerfile / docker-compose for one‑command local run.

---

## Disclaimer

This project is for learning and portfolio purposes only.  
You are responsible for complying with the Telegram Bot API and Spotify Developer Terms when deploying it publicly.