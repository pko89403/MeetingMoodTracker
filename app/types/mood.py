"""회의록 분석 엔드포인트의 요청/응답 타입 정의."""

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    """회의록 분석 요청 스키마."""

    meeting_id: str
    text: str


class AnalyzeResponse(BaseModel):
    """회의록 분석 응답 스키마."""

    topic: str
    mood: str
    confidence: float
