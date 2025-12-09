from __future__ import annotations

from uuid import uuid4

import httpx
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
)

from app.config import settings

API_BASE_URL = "http://127.0.0.1:8000"


# --- command handlers -------------------------------------------------------


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Hi! I can share your Spotify Now Playing via inline mode.\n\n"
        "1) Use /connect to link your Spotify account.\n"
        "2) Then type @%s in any chat and pick a card."
        % (context.bot.username or "this_bot")
    )
    await update.message.reply_text(text)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{API_BASE_URL}/auth/status",
                params={"telegram_id": telegram_id},
            )
    except httpx.RequestError:
        await update.message.reply_text("Backend is offline right now. Try again later.")
        return

    if resp.status_code == 200 and resp.json().get("connected"):
        await update.message.reply_text("✅ Connected to Spotify.")
    else:
        await update.message.reply_text("❌ Not connected. Use /connect.")


async def cmd_connect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{API_BASE_URL}/auth/login",
                params={"telegram_id": telegram_id},
            )
            resp.raise_for_status()
    except httpx.RequestError:
        await update.message.reply_text("Backend is offline right now. Try again later.")
        return

    auth_url = resp.json()["auth_url"]
    keyboard = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("Connect Spotify", url=auth_url),
    )
    await update.message.reply_text("Authorize with Spotify:", reply_markup=keyboard)


# --- inline handler ---------------------------------------------------------


async def handle_inline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline queries: @bot in any chat."""
    telegram_id = update.inline_query.from_user.id

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"{API_BASE_URL}/api/now-playing",
                params={"telegram_id": telegram_id},
            )
    except httpx.RequestError:
        result = InlineQueryResultArticle(
            id=str(uuid4()),
            title="Backend is offline",
            description="Cannot reach now-playing API",
            input_message_content=InputTextMessageContent(
                "Now playing service is temporarily unavailable.",
            ),
        )
        await update.inline_query.answer([result], cache_time=0)
        return

    if resp.status_code in (400, 404):
        result = InlineQueryResultArticle(
            id=str(uuid4()),
            title="Connect your Spotify account",
            description="Open a private chat with the bot and run /connect",
            input_message_content=InputTextMessageContent(
                "I need to connect my Spotify account first. "
                "Open a private chat with the bot and send /connect.",
            ),
        )
        await update.inline_query.answer([result], cache_time=0)
        return

    data = resp.json()
    if not data.get("playing"):
        result = InlineQueryResultArticle(
            id=str(uuid4()),
            title="Nothing is playing",
            description="Spotify reports no currently playing track",
            input_message_content=InputTextMessageContent(
                "Nothing is playing on my Spotify right now.",
            ),
        )
        await update.inline_query.answer([result], cache_time=5)
        return

    track = data["track"]
    artists_str = ", ".join(track["artists"])
    title = f"{artists_str} – {track['name']}"
    desc = track.get("album") or "Spotify track"
    url = track.get("url") or ""

    message_text = (
        "🎧 Now playing on Spotify:\n"
        f"*{track['name']}* by *{artists_str}*\n"
        f"Album: _{track.get('album', 'Unknown')}_\n"
        f"{url}"
    )

    result = InlineQueryResultArticle(
        id=str(uuid4()),
        title=title,
        description=desc,
        thumbnail_url=track.get("image_url") or None,
        input_message_content=InputTextMessageContent(
            message_text,
            parse_mode="Markdown",
        ),
    )

    await update.inline_query.answer([result], cache_time=5)


# --- entrypoint -------------------------------------------------------------


def main() -> None:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing in .env")

    application = ApplicationBuilder().token(settings.telegram_bot_token).build()

    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CommandHandler("connect", cmd_connect))
    application.add_handler(InlineQueryHandler(handle_inline))

    application.run_polling()


if __name__ == "__main__":
    main()
