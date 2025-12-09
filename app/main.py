from __future__ import annotations

from fastapi import FastAPI

from .db import Base, engine
from .routers.auth import router as auth_router
from .routers.now_playing import router as now_playing_router

app = FastAPI(title="Spotify Now Playing Bot API")


@app.on_event("startup")
async def on_startup() -> None:
    """Create DB tables on first start."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Routers
app.include_router(auth_router)
app.include_router(now_playing_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
