"""MeetingMoodTracker FastAPI 애플리케이션 진입점."""

from fastapi import FastAPI

from app.runtime.analyze import router as analyze_router
from app.runtime.env_config import router as env_config_router
from app.runtime.sentiment import router as sentiment_router

app = FastAPI(title="MeetingMoodTracker")

app.include_router(analyze_router, prefix="/api/v1")
app.include_router(env_config_router)
app.include_router(sentiment_router)
