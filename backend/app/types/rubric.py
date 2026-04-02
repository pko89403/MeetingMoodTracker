"""루브릭 지수 산출 요청/응답 타입 정의."""

from pydantic import BaseModel, Field

from app.types.emotion import MeetingSignals
from app.types.mood import AnalyzeSentiment, MeetingRubrics


class RubricCalculateRequest(BaseModel):
    """루브릭 지수 산출 요청 스키마."""

    topics: list[str] = Field(default_factory=list, description="추출된 주제 목록")
    sentiment: AnalyzeSentiment = Field(..., description="추출된 감정 분포")
    meeting_signals: MeetingSignals = Field(..., description="추출된 회의 시그널 (5축)")


class RubricCalculateResponse(BaseModel):
    """루브릭 지수 산출 응답 스키마."""

    rubric: MeetingRubrics
