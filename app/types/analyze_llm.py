"""Analyze LLM 단계 내부 데이터 타입 정의."""

from pydantic import BaseModel, Field


class TopicExtractionResult(BaseModel):
    """Topic 추출 단계의 JSON structured 출력 스키마."""

    topics: list[str] = Field(min_length=1)


class SentimentConfidenceRaw(BaseModel):
    """LLM이 반환하는 감정 축 confidence 원시값."""

    confidence: float


class SentimentRawResult(BaseModel):
    """LLM이 반환하는 감정 분포 원시 스키마."""

    positive: SentimentConfidenceRaw
    negative: SentimentConfidenceRaw
    neutral: SentimentConfidenceRaw


class SentimentExtractionResult(BaseModel):
    """Sentiment 추출 단계의 JSON structured 출력 스키마."""

    sentiment: SentimentRawResult
