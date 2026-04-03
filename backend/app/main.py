"""MeetingMoodTracker FastAPI 애플리케이션 진입점."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.runtime.analyze import router as analyze_router
from app.runtime.emotion import router as emotion_router
from app.runtime.env_config import router as env_config_router
from app.runtime.health import router as health_router
from app.runtime.meeting_turns import router as meeting_turns_router
from app.runtime.rubric import router as rubric_router
from app.runtime.sentiment import router as sentiment_router

app = FastAPI(title="MeetingMoodTracker")

# CORS: ALLOWED_ORIGINS 환경변수로 허용 오리진을 주입하거나, 기본값으로 로컬 개발 서버를 허용한다.
_default_origins = "http://localhost:5173,http://localhost:3000"
_allowed_origins = os.getenv("ALLOWED_ORIGINS", _default_origins).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router, prefix="/api/v1")
app.include_router(emotion_router)
app.include_router(env_config_router)
app.include_router(sentiment_router)
app.include_router(meeting_turns_router)
app.include_router(rubric_router)
app.include_router(health_router)
