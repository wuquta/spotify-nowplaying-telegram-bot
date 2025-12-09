from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load local .env if present
load_dotenv()


@dataclass
class Settings:
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

    spotify_client_id: str = os.getenv("SPOTIFY_CLIENT_ID", "")
    spotify_client_secret: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    spotify_redirect_uri: str = os.getenv(
        "SPOTIFY_REDIRECT_URI",
        "http://127.0.0.1:8000/auth/callback",
    )

    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./data.db",
    )


settings = Settings()
