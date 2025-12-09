from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models import User
from ..spotify_client import get_currently_playing

router = APIRouter(prefix="/api", tags=["now-playing"])


@router.get("/now-playing")
async def now_playing(
    telegram_id: int = Query(..., ge=1),
    session: AsyncSession = Depends(get_session),
):
    """Return info about the user's currently playing Spotify track."""
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Unknown Telegram user")

    if not user.access_token or not user.spotify_user_id:
        raise HTTPException(status_code=400, detail="Spotify account is not linked yet")

    track = await get_currently_playing(user.access_token)

    if track is None:
        return {"playing": False, "track": None}

    return {"playing": True, "track": track}
