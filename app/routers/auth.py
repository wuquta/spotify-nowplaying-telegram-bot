from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models import User
from ..spotify_client import (
    build_authorize_url,
    exchange_code_for_tokens,
    fetch_current_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login(
    telegram_id: int = Query(..., ge=1),
    session: AsyncSession = Depends(get_session),
):
    """Return Spotify authorize URL for a given Telegram user."""
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(telegram_id=telegram_id)
        session.add(user)
        await session.commit()

    auth_url = build_authorize_url(state=str(telegram_id))
    return {"auth_url": auth_url}


@router.get("/status")
async def status(
    telegram_id: int = Query(..., ge=1),
    session: AsyncSession = Depends(get_session),
):
    """Tell if the Telegram user is linked to a Spotify account."""
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Unknown Telegram user")

    connected = bool(user.spotify_user_id and user.access_token)
    return {
        "connected": connected,
        "spotify_user_id": user.spotify_user_id,
    }


@router.get("/callback", response_class=HTMLResponse)
async def callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """Spotify redirects here after user authorizes or denies access."""
    if error:
        return HTMLResponse(
            f"<h3>Spotify authorization failed</h3><p>Error: {error}</p>",
            status_code=400,
        )

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    try:
        telegram_id = int(state)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid state")

    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Unknown Telegram user")

    token_data = await exchange_code_for_tokens(code)
    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")
    expires_at = token_data.get("expires_at")

    if isinstance(expires_at, datetime):
        user.expires_at = expires_at

    profile = await fetch_current_user(access_token)

    user.spotify_user_id = profile.get("id")
    user.access_token = access_token
    if refresh_token:
        user.refresh_token = refresh_token

    await session.commit()

    html = """
    <html>
      <head><title>Spotify connected</title></head>
      <body>
        <h2>Spotify account linked ✅</h2>
        <p>You can close this page and go back to Telegram.</p>
      </body>
    </html>
    """
    return HTMLResponse(html)
