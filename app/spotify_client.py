from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import base64
import httpx

from .config import settings

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
ME_URL = "https://api.spotify.com/v1/me"
CURRENTLY_PLAYING_URL = "https://api.spotify.com/v1/me/player/currently-playing"

SCOPES = [
    "user-read-currently-playing",
    "user-read-recently-played",
]


def build_authorize_url(state: str) -> str:
    """Build Spotify OAuth authorize URL for Authorization Code flow."""
    from urllib.parse import urlencode

    params = {
        "client_id": settings.spotify_client_id,
        "response_type": "code",
        "redirect_uri": settings.spotify_redirect_uri,
        "scope": " ".join(SCOPES),
        "state": state,
        "show_dialog": "false",
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def _basic_auth_header() -> str:
    raw = f"{settings.spotify_client_id}:{settings.spotify_client_secret}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("utf-8")


async def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
    """Exchange authorization code for access/refresh tokens."""
    headers = {
        "Authorization": _basic_auth_header(),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.spotify_redirect_uri,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(TOKEN_URL, data=data, headers=headers)
        resp.raise_for_status()
        payload = resp.json()

    expires_in = int(payload.get("expires_in", 3600))
    payload["expires_at"] = datetime.utcnow() + timedelta(seconds=expires_in)
    return payload


async def fetch_current_user(access_token: str) -> Dict[str, Any]:
    """Return Spotify profile (`/me`) for given access token."""
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(ME_URL, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def get_currently_playing(access_token: str) -> Optional[Dict[str, Any]]:
    """Return normalized info about the currently playing track.

    Returns None if nothing is playing (204) or there is no track.
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(CURRENTLY_PLAYING_URL, headers=headers)

    if resp.status_code == 204:
        return None

    resp.raise_for_status()
    payload = resp.json()

    item = payload.get("item")
    if not item:
        return None

    artists = [a["name"] for a in item.get("artists", [])]
    album = item.get("album", {})
    images = album.get("images", [])

    return {
        "name": item.get("name"),
        "artists": artists,
        "album": album.get("name"),
        "url": item.get("external_urls", {}).get("spotify"),
        "image_url": images[0]["url"] if images else None,
        "is_playing": payload.get("is_playing", False),
        "progress_ms": payload.get("progress_ms"),
        "duration_ms": item.get("duration_ms"),
    }
