"""Analyze inspect/stream 라우트에서 사용하는 타입 정의."""

from typing import Literal

from pydantic import BaseModel, Field

from app.types.mood import AnalyzeResponse


class AnalyzeLogicStep(BaseModel):
    """analyze 파이프라인의 고정 로직 단계를 표현한다."""

    step_id: str = Field(min_length=1)
    title_ko: str = Field(min_length=1)
    description_ko: str = Field(min_length=1)


class AnalyzeLogEntry(BaseModel):
    """단일 analyze 요청에서 생성된 로그 항목을 표현한다."""

    request_id: str = Field(min_length=1)
    step_id: str = Field(min_length=1)
    message_ko: str = Field(min_length=1)
    created_at: str = Field(min_length=1)


class AnalyzeInspectResponse(BaseModel):
    """`POST /api/v1/analyze/inspect` 응답 스키마."""

    request_id: str = Field(min_length=1)
    result: AnalyzeResponse
    logic_steps: list[AnalyzeLogicStep]
    logs: list[AnalyzeLogEntry]


AnalyzeSseEventType = Literal["start", "log", "result", "done", "error"]


class AnalyzeSseEventPayload(BaseModel):
    """SSE 이벤트의 data 필드로 직렬화되는 페이로드."""

    event: AnalyzeSseEventType
    request_id: str = Field(min_length=1)
    step_id: str | None = None
    message_ko: str | None = None
    created_at: str | None = None
    result: AnalyzeResponse | None = None
    logic_steps: list[AnalyzeLogicStep] | None = None
