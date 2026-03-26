from fastapi import FastAPI

from app.runtime.analyze import router as analyze_router

app = FastAPI(title="MeetingMoodTracker")

app.include_router(analyze_router, prefix="/api/v1")
