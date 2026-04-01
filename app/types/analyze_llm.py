"""Analyze LLM 단계 내부 데이터 타입 정의."""

from pydantic import BaseModel, Field


class TopicCandidateResult(BaseModel):
    """Topic 후보 단일 항목의 JSON structured 출력 스키마."""

    label: str = Field(min_length=1, max_length=60)
    confidence: float


class TopicExtractionResult(BaseModel):
    """Topic 추출 단계의 JSON structured 출력 스키마."""

    topics: list[TopicCandidateResult] = Field(min_length=1, max_length=3)


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


class EmotionConfidenceRaw(BaseModel):
    """LLM이 반환하는 정서 축 confidence 원시값."""

    confidence: float


class EmotionRawResult(BaseModel):
    """LLM이 반환하는 기본 8정서 분포 원시 스키마."""

    anger: EmotionConfidenceRaw
    joy: EmotionConfidenceRaw
    sadness: EmotionConfidenceRaw
    neutral: EmotionConfidenceRaw
    anxiety: EmotionConfidenceRaw
    frustration: EmotionConfidenceRaw
    excitement: EmotionConfidenceRaw
    confusion: EmotionConfidenceRaw


class EmotionExtractionResult(BaseModel):
    """Emotion 추출 단계의 JSON structured 출력 스키마."""

    emotions: EmotionRawResult
